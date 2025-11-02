#! /usr/bin/env python3

"""Shell for debugging containers using Pebble."""

from __future__ import annotations

import datetime
import glob
import importlib
import json
import os
import pkgutil
import re
import shlex
import shutil
import subprocess
import sys
import time

import ops
import rich
import shimmer
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import commands
from .commands._base import Command
from .utils import (
    PipelineExecutor,
    format_error,
    get_shell_history,
    get_shell_parser,
    init_shell_history,
    init_shell_parser,
    setup_readline_support,
)


class PebbleShell:
    """A shell interface for debugging containers using Pebble."""

    def __init__(self, client: ops.pebble.Client | shimmer.PebbleCliClient):
        self.client = client
        self.commands: dict[str, Command] = {}
        self.readline_wrapper = None
        self.executor = None
        self.console = Console()
        self.error_console = Console(stderr=True)
        # Will be set in _setup_commands()
        self.alias_command = None
        self._setup_commands()
        self.last_exit_code = 0

        # Initialise history and parser.
        init_shell_history()
        init_shell_parser()

        # Detect remote user and set HOME
        user = self._get_remote_user()
        self.home_dir = f"/home/{user}" if user else "/root"
        self.current_directory = self.home_dir

        # Set HOME and PWD in shell variables.
        parser = get_shell_parser()
        parser.set_variable("HOME", self.home_dir)
        parser.set_variable("PWD", self.home_dir)
        parser.set_variable("USER", user or "root")

    def _get_remote_user(self) -> str:
        try:
            with self.client.pull("/proc/self/status") as f:
                content = f.read()
            assert isinstance(
                content, str
            )  # TODO: I think shimmer has a bug that makes this required (same elsewhere).
        except ops.pebble.PathError:
            return "?"
        for line in content.splitlines():
            if line.startswith("Uid:"):
                uid = line.split()[1]
                break
        else:
            return "?"
        try:
            with self.client.pull("/etc/passwd") as f:
                content = f.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            return uid
        for line in content.splitlines():
            parts = line.split(":")
            if len(parts) >= 3 and parts[2] == uid:
                return parts[0]
        return "?"

    def _discover_commands(self) -> None:
        """Import all command modules to trigger auto-registration."""
        for _, modname, ispkg in pkgutil.iter_modules(commands.__path__):
            if ispkg:
                # Skip sub-packages if any.
                continue
            try:
                importlib.import_module(f".commands.{modname}", package=__package__)
            except ImportError as e:
                # Log import errors but continue with other modules.
                self.console.print(
                    f"Warning: Could not import command module {modname}: {e}"
                )

    def _setup_commands(self) -> None:
        """Set up available commands via auto-discovery."""
        self._discover_commands()

        # Get all registered command classes and instantiate them.
        self.commands = {}
        for command_name, command_class in Command.get_all_commands().items():
            try:
                self.commands[command_name] = command_class(self)
            except Exception as e:  # noqa: PERF203  # needed for command loading
                # Log instantiation errors but continue with other commands.
                self.console.print(
                    f"Warning: Could not instantiate command {command_name}: {e}"
                )

        # Special handling for alias command.
        self.alias_command = self.commands["alias"]

    def connect(self) -> bool:
        """Connect to Pebble.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.get_system_info()
            return True
        except (ops.pebble.ConnectionError, FileNotFoundError) as e:
            self.console.print(
                Panel(
                    Text(
                        format_error(f"Failed to connect to Pebble: {e}"),
                        style="bold red",
                    ),
                    title="[b red]Connection Error[/b red]",
                    style="red",
                )
            )
            return False

    def run_command(self, command_line: str) -> bool:
        """Run a command with support for pipes, redirection, chaining, and for loops.

        Args:
            command_line: The command line to execute

        Returns:
            True to continue shell, False to exit
        """
        if not command_line.strip():
            return True

        # Check for for loop syntax.
        if command_line.strip().startswith("for "):
            return self._execute_for_loop(command_line)

        history = get_shell_history()
        try:
            expanded_command = history.expand_history(command_line.strip())
            if expanded_command != command_line.strip():
                self.console.print(
                    Panel(
                        Text(expanded_command, style="yellow"),
                        title="[b]History Expansion[/b]",
                        style="bold yellow",
                    )
                )
        except Exception as e:
            from .utils.history import HistoryExpansionError

            if isinstance(e, HistoryExpansionError):
                self.console.print(
                    Panel(
                        Text(
                            format_error(f"History expansion error: {e}"),
                            style="bold red",
                        ),
                        title="[b red]History Error[/b red]",
                        style="red",
                    )
                )
                return True
            raise

        if "=" in expanded_command and not expanded_command.startswith("alias"):
            parts = expanded_command.split("=", 1)
            if len(parts) == 2 and parts[0].strip() and " " not in parts[0]:
                var_name = parts[0].strip()
                var_value = parts[1].strip()
                parser = get_shell_parser()
                parser.set_variable(var_name, var_value)
                self.console.print(
                    f"[cyan]{var_name}[/cyan]=[white]{var_value}[/white]"
                )
                return True

        alias_expanded_command = self.alias_command.expand_alias(expanded_command)
        history.add_command(command_line.strip())

        try:
            parser = get_shell_parser()
            parsed_commands = parser.parse_command_line(alias_expanded_command)

            if not parsed_commands:
                return True

            if self.executor is None:
                assert self.client is not None
                self.executor = PipelineExecutor(
                    self.commands, self.alias_command, self
                )

            start_time = time.perf_counter()
            result = self.executor.execute_pipeline(parsed_commands)
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            # Get last exit code from parser.
            self.last_exit_code = parser.get_exit_code()
            if elapsed >= 0.5:
                self.console.print(
                    f"[dim]Command executed in {elapsed:.3f} seconds[/dim]"
                )
            return result

        except Exception as e:
            self.console.print(
                Panel(
                    Text(format_error(f"Error parsing command: {e}"), style="bold red"),
                    title="[b red]Parse Error[/b red]",
                    style="red",
                )
            )

            self.console.print_exception()
            return True

    def _execute_for_loop(self, command_line: str) -> bool:
        """Execute a for loop command.

        Syntax: for <var> in <list>; do <commands>; done

        Args:
            command_line: The for loop command line

        Returns:
            True to continue shell, False to exit
        """
        # Parse for loop syntax: for <var> in <list>; do <commands>; done
        pattern = r"for\s+(\w+)\s+in\s+(.+?);\s*do\s+(.+?);\s*done"
        match = re.match(pattern, command_line, re.DOTALL)

        if not match:
            self.console.print(
                Panel(
                    Text(
                        format_error(
                            "Invalid for loop syntax. Use: for <var> in <list>; do <commands>; done"
                        ),
                        style="bold red",
                    ),
                    title="[b red]For Loop Error[/b red]",
                    style="red",
                )
            )
            return True

        var_name = match.group(1)
        list_expr = match.group(2).strip()
        commands = match.group(3).strip()

        # Parse the list expression.
        try:
            # Handle different list formats.
            if list_expr.startswith('"') and list_expr.endswith('"'):
                # Quoted string with space-separated values.
                items = shlex.split(list_expr)
            elif list_expr.startswith("(") and list_expr.endswith(")"):
                # Parenthesised list.
                items = shlex.split(list_expr[1:-1])
            elif list_expr.startswith("{") and list_expr.endswith("}"):
                # Brace expansion (simple).
                content = list_expr[1:-1]
                items = [item.strip() for item in content.split(",")]
            else:
                # Space-separated values.
                items = shlex.split(list_expr)
        except Exception as e:
            self.console.print(
                Panel(
                    Text(
                        format_error(f"Error parsing list expression: {e}"),
                        style="bold red",
                    ),
                    title="[b red]For Loop Error[/b red]",
                    style="red",
                )
            )
            return True

        # Execute commands for each item.
        parser = get_shell_parser()
        total_exit_code = 0

        for item in items:
            parser.set_variable(var_name, item)

            try:
                parsed_commands = parser.parse_command_line(commands)

                if parsed_commands:
                    if self.executor is None:
                        assert self.client is not None
                        self.executor = PipelineExecutor(
                            self.commands, self.alias_command, self
                        )

                    result = self.executor.execute_pipeline(parsed_commands)
                    if not result:  # Exit requested
                        return False

                    exit_code = parser.get_exit_code()
                    if exit_code != 0:
                        total_exit_code = exit_code

            except Exception as e:
                self.console.print(
                    Panel(
                        Text(
                            format_error(f"Error executing for loop command: {e}"),
                            style="bold red",
                        ),
                        title="[b red]For Loop Error[/b red]",
                        style="red",
                    )
                )
                total_exit_code = 1

        self.last_exit_code = total_exit_code
        return True

    def _get_system_info(self):
        """Get comprehensive system information for welcome message as a rich Table."""
        if not self.client:
            return Table()

        table = Table(show_header=False, box=None, expand=False, padding=(0, 1))
        table.add_column("Field", style="bold cyan", no_wrap=True)
        table.add_column("Value", style="white")

        current_time = datetime.datetime.now().strftime("%a %b %d %H:%M:%S UTC %Y")
        table.add_row("System time", current_time)

        try:
            with self.client.pull("/proc/loadavg") as f:
                content = f.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            table.add_row("System load", "[dim]unavailable[/dim]")
        else:
            load_avg = content.split()[0]
            table.add_row("System load", load_avg)

        try:
            with self.client.pull("/proc/meminfo") as f:
                content = f.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            table.add_row("Memory usage", "[dim]unavailable[/dim]")
        else:
            mem_total = 0
            mem_available = 0
            for line in content.splitlines():
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            if mem_total > 0:
                used_memory = mem_total - mem_available
                memory_percent = (used_memory / mem_total) * 100
                table.add_row("Memory usage", f"{memory_percent:.0f}%")
            else:
                table.add_row("Memory usage", "[dim]unavailable[/dim]")

        try:
            with self.client.pull("/proc/meminfo") as f:
                content = f.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            table.add_row("Swap usage", "[dim]unavailable[/dim]")
        else:
            swap_total = 0
            swap_free = 0
            for line in content.splitlines():
                if line.startswith("SwapTotal:"):
                    swap_total = int(line.split()[1])
                elif line.startswith("SwapFree:"):
                    swap_free = int(line.split()[1])
            if swap_total > 0:
                swap_used = swap_total - swap_free
                swap_percent = (swap_used / swap_total) * 100
                table.add_row("Swap usage", f"{swap_percent:.0f}%")
            else:
                table.add_row("Swap usage", "0%")

        try:
            proc_entries = self.client.list_files("/proc")
        except ops.pebble.PathError:
            table.add_row("Processes", "[dim]unavailable[/dim]")
        else:
            process_count = sum(1 for entry in proc_entries if entry.name.isdigit())
            table.add_row("Processes", str(process_count))

        system_info = self.client.get_system_info()
        table.add_row("Pebble version", str(system_info.version))

        services = self.client.get_services()
        running = sum(1 for service in services if service.is_running())
        table.add_row("Pebble services", f"{running}/{len(services)} running")

        checks = self.client.get_checks()
        up = sum(1 for check in checks if check.status == ops.pebble.CheckStatus.UP)
        table.add_row("Pebble checks", f"{up}/{len(checks)} up")

        notices = self.client.get_notices(types=[ops.pebble.NoticeType.CUSTOM])
        table.add_row("Pebble custom notices", str(len(notices)))

        # Last login:
        try:
            with self.client.pull("/var/log/auth.log") as f:
                content = f.read()
            assert isinstance(content, str)
        except ops.pebble.PathError:
            table.add_row("Last login", "[dim]unavailable[/dim]")
        else:
            auth_lines = content.splitlines()
            if auth_lines:
                for line in reversed(auth_lines[-50:]):
                    if "session opened" in line.lower() or "accepted" in line.lower():
                        parts = line.split()
                        if len(parts) >= 3:
                            timestamp = " ".join(parts[:3])
                            table.add_row("Last login", timestamp)
                            break

        return table

    def run(self):
        """Run the interactive shell."""
        rich.print(
            Panel(
                Text("Cascade - commands flowing over bare rocks", style="bold cyan"),
                title="[b]Cascade Shell[/b]",
                subtitle="Type 'help' for available commands, 'exit' to quit.",
                style="bold blue",
            )
        )

        if not self.connect():
            sys.exit(1)

        rich.print(
            Panel(
                Text("Connected to Pebble successfully!", style="green"),
                style="bold green",
            )
        )

        rich.print(
            Panel(self._get_system_info(), title="System Info", style="bold magenta")
        )

        assert self.client is not None
        self.readline_wrapper = setup_readline_support(
            self.commands, self.alias_command, self
        )
        self.executor = PipelineExecutor(self.commands, self.alias_command, self)
        parser = get_shell_parser()
        parser.update_pwd(self.current_directory)

        if self.readline_wrapper.has_readline:
            history = get_shell_history()
            for command in history.get_history():
                self.readline_wrapper.add_history(command)

        while True:
            try:
                current_dir = self.current_directory
                if hasattr(self, "last_exit_code") and self.last_exit_code == 0:
                    status_text = Text("✔", style="green")
                else:
                    status_text = Text("✖", style="red")

                # Show ~ in prompt when relevant:
                if current_dir == self.home_dir:
                    display_dir = "~"
                elif current_dir.startswith(self.home_dir + "/"):
                    display_dir = "~" + current_dir[len(self.home_dir) :]
                else:
                    display_dir = current_dir

                if display_dir == "/":
                    prompt_text = Text.assemble(status_text, " cascade:/> ")
                else:
                    prompt_text = Text.assemble(status_text, f" cascade:{display_dir}> ")

                # Render the prompt using Rich's console to handle color support
                prompt = self.console.render_str(prompt_text)

                if self.readline_wrapper:
                    command_line = self.readline_wrapper.input_with_prompt(prompt)
                else:
                    command_line = self.console.input(prompt_text)

                if self.readline_wrapper and command_line.strip():
                    self.readline_wrapper.add_history(command_line)

                if not self.run_command(command_line):
                    break
            except KeyboardInterrupt:
                self.console.print("[yellow]\nUse 'exit' to quit.[/yellow]")
                continue
            except EOFError:
                self.console.print("[bold magenta]\nGoodbye![/bold magenta]")
                break


def discover_pebble_sockets() -> list[str]:
    """Discover available Pebble sockets in /charm/<container>/pebble.sock pattern.

    Returns:
        List of available socket paths
    """
    socket_pattern = "/charm/*/pebble.sock"
    available_sockets = [
        socket_path
        for socket_path in glob.glob(socket_pattern)
        if os.path.exists(socket_path) and os.access(socket_path, os.R_OK)
    ]

    return sorted(available_sockets)


def select_socket_interactively(sockets: list[str]) -> str | None:
    """Prompt user to select a socket from available options.

    Args:
        sockets: List of available socket paths

    Returns:
        Selected socket path or None if user chooses to exit
    """
    console = Console()

    console.print(
        Panel(
            "Multiple Pebble sockets found. Please select one:",
            title="[b]Socket Selection[/b]",
            style="bold blue",
        )
    )

    # Display options:
    for i, socket in enumerate(sockets, 1):
        container_name = socket.split("/")[2]  # Extract container name from path
        console.print(f"  {i}. {container_name} ({socket})")

    console.print(f"  {len(sockets) + 1}. Exit")

    while True:
        try:
            choice = console.input("\nEnter your choice (number): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(sockets):
                return sockets[choice_num - 1]
            elif choice_num == len(sockets) + 1:
                return None
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
        except (ValueError, KeyboardInterrupt):  # noqa: PERF203  # needed for input handling
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except EOFError:
            return None


def check_juju_available() -> bool:
    """Check if a Juju CLI executable is available."""
    return shutil.which("juju") is not None


def get_juju_units_and_containers() -> list[dict]:
    """Get list of units and their containers from juju status.

    Returns:
        List of dictionaries with unit and container information
    """
    try:
        result = subprocess.run(
            ["juju", "status", "--format=json"],  # noqa: S607 # juju expected to be in PATH
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        status_data = json.loads(result.stdout)
    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ) as e:
        console = Console()
        console.print(f"[red]Error getting juju status: {e}[/red]")
        return []

    units_containers = []

    # Parse applications and their units:
    applications = status_data.get("applications", {})
    for app_name, app_data in applications.items():
        units = app_data.get("units", {})
        for unit_name, unit_data in units.items():
            # Check if unit has containers (charm uses Pebble):
            if "containers" in unit_data:
                containers = unit_data["containers"]
                units_containers.extend(
                    {
                        "unit": unit_name,
                        "container": container_name,
                        "application": app_name,
                    }
                    for container_name in containers
                )

    return units_containers


def select_juju_unit_container(units_containers: list[dict]) -> dict | None:
    """Prompt user to select a unit and container from juju.

    Args:
        units_containers: List of unit/container combinations

    Returns:
        Selected unit/container dict or None if user chooses to exit
    """
    console = Console()

    console.print(
        Panel(
            "No direct Pebble sockets found, but Juju is available.\n"
            "Please select a unit and container to connect via Juju SSH:",
            title="[b]Juju Connection[/b]",
            style="bold yellow",
        )
    )

    for i, uc in enumerate(units_containers, 1):
        console.print(
            f"  {i}. {uc['unit']} / {uc['container']} (app: {uc['application']})"
        )

    console.print(f"  {len(units_containers) + 1}. Exit")

    while True:
        try:
            choice = console.input("\nEnter your choice (number): ").strip()
            choice_num = int(choice)

            if 1 <= choice_num <= len(units_containers):
                return units_containers[choice_num - 1]
            elif choice_num == len(units_containers) + 1:
                return None
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
        except (ValueError, KeyboardInterrupt):  # noqa: PERF203  # needed for input handling
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except EOFError:
            return None


def create_juju_pebble_client(unit: str, container: str) -> shimmer.PebbleCliClient:
    """Create a PebbleCliClient that uses juju ssh to communicate with Pebble.

    Args:
        unit: Juju unit name (e.g., "myapp/0")
        container: Container name

    Returns:
        Configured PebbleCliClient
    """
    pebble_binary = f"juju ssh {unit} PEBBLE_SOCKET=/charm/containers/{container}/pebble.socket /charm/bin/pebble"

    return shimmer.PebbleCliClient(
        socket_path="",
        pebble_binary=pebble_binary,
        timeout=60.0,
    )


def main(
    socket: str = typer.Option(
        "/charm/containers/*/pebble.socket",
        "--socket",
        help="Path to Pebble socket",
    ),
    pebble_cli: str = typer.Option(
        "",
        "--pebble-cli",
        help="Use the Pebble CLI rather than a direct socket connection",
    ),
    command_file: str | None = typer.Option(
        None,
        "-c",
        "--command-file",
        help="Path to a file containing Cascade commands to execute non-interactively",
    ),
):
    """Cascade - commands flowing over bare rocks."""
    socket_path = socket

    # If default socket pattern and no user-specified socket, try socket discovery.
    if socket_path == "/charm/containers/*/pebble.socket":
        # First try the default pattern locations:
        default_sockets = glob.glob(socket_path)
        accessible_defaults = [
            s for s in default_sockets if os.path.exists(s) and os.access(s, os.R_OK)
        ]

        if accessible_defaults:
            if len(accessible_defaults) == 1:
                socket_path = accessible_defaults[0]
            else:
                socket_path = select_socket_interactively(accessible_defaults)
                if socket_path is None:
                    sys.exit(1)
        else:
            discovered_sockets = discover_pebble_sockets()

            if not discovered_sockets:
                if check_juju_available():
                    units_containers = get_juju_units_and_containers()

                    if not units_containers:
                        console = Console()
                        console.print(
                            Panel(
                                "No accessible Pebble sockets found locally, and no Juju units with containers found.\n"
                                "Please ensure Pebble is running and accessible, or specify a socket path with --socket.",
                                title="[b red]No Sockets Found[/b red]",
                                style="red",
                            )
                        )
                        sys.exit(1)

                    selected = select_juju_unit_container(units_containers)
                    if selected is None:
                        sys.exit(1)

                    # Type assertion: selected is guaranteed to be a dict here
                    assert selected is not None

                    console = Console()
                    console.print(
                        Panel(
                            f"[yellow]Performance Warning:[/yellow] Using Juju SSH connection to {selected['unit']}/{selected['container']}.\n"
                            "This method has higher latency than direct socket connections but provides most functionality.",
                            title="[b yellow]Juju SSH Connection[/b yellow]",
                            style="yellow",
                        )
                    )

                    client = create_juju_pebble_client(
                        selected["unit"], selected["container"]
                    )
                    shell = PebbleShell(client)

                    if not command_file:
                        shell.run()
                        return
                    try:
                        if command_file == "-":
                            lines = sys.stdin
                            for line in lines:
                                line = line.strip()
                                if not line or line.startswith("#"):
                                    continue
                                shell.run_command(line)
                        else:
                            with open(command_file) as f:
                                for line in f:
                                    line = line.strip()
                                    if not line or line.startswith("#"):
                                        continue
                                    shell.run_command(line)
                    except Exception as e:
                        print(f"Error reading command file: {e}")
                        sys.exit(1)
                    sys.exit(0)
                console = Console()
                console.print(
                    Panel(
                        "No accessible Pebble sockets found.\n"
                        "Please ensure Pebble is running and accessible, install Juju for remote access, or specify a socket path with --socket.",
                        title="[b red]No Sockets Found[/b red]",
                        style="red",
                    )
                )
                sys.exit(1)
            elif len(discovered_sockets) == 1:
                socket_path = discovered_sockets[0]
                console = Console()
                container_name = socket_path.split("/")[2]
                console.print(
                    Panel(
                        f"Using Pebble socket for container: {container_name}",
                        title="[b green]Socket Found[/b green]",
                        style="green",
                    )
                )
            else:
                socket_path = select_socket_interactively(discovered_sockets)
                if socket_path is None:
                    sys.exit(1)

    # Type assertion: socket_path is guaranteed to be a str here
    assert socket_path is not None

    if pebble_cli:
        client = shimmer.PebbleCliClient(
            socket_path=socket_path,
            pebble_binary=pebble_cli,
            timeout=30.0,
        )
    else:
        client = ops.pebble.Client(socket_path=socket_path)
    shell = PebbleShell(client)

    if not command_file:
        shell.run()
        return

    try:
        if command_file == "-":
            lines = sys.stdin
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                shell.run_command(line)
        else:
            with open(command_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    shell.run_command(line)
    except Exception as e:
        print(f"Error reading command file: {e}")
        sys.exit(1)
    sys.exit(0)


app = typer.Typer(help="Cascade - Shell for debugging containers using Pebble")
app.command()(main)


if __name__ == "__main__":
    app()
