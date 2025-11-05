"""Command executor for handling pipes, redirection, and advanced shell features."""

from __future__ import annotations

import contextlib
import io
import re
import sys
from typing import TYPE_CHECKING

import ops
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .parser import CommandType, ParsedCommand, get_shell_parser
from .pathutils import resolve_path

if TYPE_CHECKING:
    from ..commands import AliasCommand, Command
    from ..shell import PebbleShell


class CommandOutput:
    """Captures command output for piping."""

    def __init__(self):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.exit_code = 0

    def get_stdout(self) -> str:
        """Get captured stdout."""
        return self.stdout.getvalue()

    def get_stderr(self) -> str:
        """Get captured stderr."""
        return self.stderr.getvalue()

    def write_stdout(self, text: str, end: str = ""):
        """Write to stdout."""
        self.stdout.write(text + end)

    def write_stderr(self, text: str, end: str = ""):
        """Write to stderr."""
        self.stderr.write(text + end)


class PipelineExecutor:
    """Executes command pipelines with redirection support."""

    def __init__(
        self,
        commands: dict[str, Command],
        alias_command: AliasCommand,
        shell: PebbleShell,
    ):
        self.client = shell.client
        self._shell = shell
        self.console = shell.console
        self.commands = commands
        self.alias_command = alias_command
        self.parser = get_shell_parser()

    def execute_pipeline(self, parsed_commands: list[ParsedCommand]) -> bool:
        """Execute a pipeline of commands.

        Args:
            parsed_commands: List of parsed commands to execute

        Returns:
            True to continue shell, False to exit
        """
        if not parsed_commands:
            return True

        i = 0
        while i < len(parsed_commands):
            cmd = parsed_commands[i]

            if cmd.command == "exit":
                return False

            # Execute command or pipeline.
            exit_code = self._execute_command_sequence(cmd)
            self.parser.set_exit_code(exit_code)

            # Handle command chaining.
            if cmd.type == CommandType.AND:
                if exit_code != 0:
                    # Skip next command group on failure
                    i = self._skip_to_next_group(parsed_commands, i)
                    continue
            elif cmd.type == CommandType.OR:
                if exit_code == 0:
                    # Skip next command group on success.
                    i = self._skip_to_next_group(parsed_commands, i)
                    continue
            elif cmd.type == CommandType.SEMICOLON:
                # Always continue to next command
                pass

            i += 1

        return True

    def _execute_command_sequence(self, start_cmd: ParsedCommand) -> int:
        """Execute a sequence of piped commands.

        Args:
            start_cmd: First command in the sequence

        Returns:
            Exit code of the last command
        """
        # Collect all commands in the pipe sequence.
        pipe_commands: list[ParsedCommand] = []
        current = start_cmd
        while current:
            pipe_commands.append(current)
            if current.type == CommandType.PIPE:
                current = current.next_command
            else:
                break

        if len(pipe_commands) == 1:
            # Single command, handle redirection.
            return self._execute_single_command(pipe_commands[0])
        # Pipeline of commands.
        return self._execute_pipeline(pipe_commands)

    def _execute_single_command(self, cmd: ParsedCommand) -> int:
        """Execute a single command with possible redirection.

        Args:
            cmd: Command to execute

        Returns:
            Exit code
        """
        output = CommandOutput()
        exit_code = self._run_command(cmd, None, output)

        # Handle redirection
        if cmd.type == CommandType.REDIRECT_OUT and cmd.target:
            self._write_to_file(cmd.target, output.get_stdout(), append=False)
        elif cmd.type == CommandType.REDIRECT_APPEND and cmd.target:
            self._write_to_file(cmd.target, output.get_stdout(), append=True)
        elif cmd.type == CommandType.REDIRECT_IN and cmd.target:
            # Input redirection is handled in _run_command
            pass
        else:
            # No redirection, print to console
            stdout_content = output.get_stdout()
            stderr_content = output.get_stderr()

            if stdout_content:
                print(stdout_content, end="")
            if stderr_content:
                print(stderr_content, end="", file=sys.stderr)

        return exit_code

    def _execute_pipeline(self, pipe_commands: list[ParsedCommand]) -> int:
        """Execute a pipeline of commands.

        Args:
            pipe_commands: List of commands in the pipeline

        Returns:
            Exit code of the last command
        """
        # Start with no input
        pipe_input = None
        exit_code = 0

        for i, cmd in enumerate(pipe_commands):
            output = CommandOutput()

            # Execute command with input from previous command.
            exit_code = self._run_command(cmd, pipe_input, output)

            # If this is the last command, handle output redirection.
            if i == len(pipe_commands) - 1:
                if cmd.type == CommandType.REDIRECT_OUT and cmd.target:
                    self._write_to_file(cmd.target, output.get_stdout(), append=False)
                elif cmd.type == CommandType.REDIRECT_APPEND and cmd.target:
                    self._write_to_file(cmd.target, output.get_stdout(), append=True)
                else:
                    # Print final output.
                    stdout_content = output.get_stdout()
                    stderr_content = output.get_stderr()

                    if stdout_content:
                        print(stdout_content, end="")
                    if stderr_content:
                        print(stderr_content, end="", file=sys.stderr)
            else:
                # Use output as input for next command.
                pipe_input = output.get_stdout()

        return exit_code

    def _run_command(
        self, cmd: ParsedCommand, pipe_input: str | None, output: CommandOutput
    ) -> int:
        """Run a single command with input/output capture.

        Args:
            cmd: Command to run
            pipe_input: Input from previous command in pipeline
            output: Output capture object

        Returns:
            Exit code
        """
        try:
            # Handle special commands
            if cmd.command == "help":
                if cmd.args:
                    self._show_help(output, group=" ".join(cmd.args))
                else:
                    self._show_help(output)
                return 0
            if cmd.command == "clear":
                print("\033[2J\033[H", end="")
                return 0

            # Handle input redirection
            if cmd.type == CommandType.REDIRECT_IN and cmd.target:
                pipe_input = self._read_from_file(cmd.target)

            # Create a custom command instance that handles piped input
            try:
                command_instance = self.commands[cmd.command]
            except KeyError:
                output.write_stderr(f"Command not found: {cmd.command}\n")
                return 1

            # Redirect stdout to capture output
            with (
                contextlib.redirect_stdout(output.stdout),
                contextlib.redirect_stderr(output.stderr),
            ):
                try:
                    # If command supports piped input, modify args
                    args = cmd.args.copy()
                    if pipe_input and cmd.command in ["grep", "wc", "sort", "cut"]:
                        # Special handling for text processing commands
                        self._handle_piped_text_command(cmd, pipe_input, output)
                        return 0
                    else:
                        # Regular command execution
                        return command_instance.execute(self.client, args)

                except (ops.pebble.PathError, FileNotFoundError) as e:
                    output.write_stderr(f"Path error: {e}\n")
                    return 1
                except PermissionError as e:
                    output.write_stderr(f"Permission denied: {e}\n")
                    return 1
                except Exception as e:
                    output.write_stderr(f"Error executing command: {e}\n")
                    self.console.print_exception(show_locals=True)
                    return 1

        except Exception as e:
            output.write_stderr(f"Execution error: {e}\n")
            self.console.print_exception(show_locals=True)
            return 1
        return 0

    def _handle_piped_text_command(
        self, cmd: ParsedCommand, pipe_input: str, output: CommandOutput
    ) -> None:
        """Handle text processing commands with piped input."""
        lines = pipe_input.splitlines()

        if cmd.command == "grep":
            if not cmd.args:
                output.write_stderr("grep: missing pattern\n")
                return

            pattern = cmd.args[0]

            try:
                if pattern.startswith("/") and pattern.endswith("/"):
                    regex = re.compile(pattern[1:-1])
                else:
                    regex = re.compile(re.escape(pattern))

                for line in lines:
                    if regex.search(line):
                        output.write_stdout(f"{line}\n")
            except re.error:
                output.write_stderr(f"grep: invalid pattern: {pattern}\n")

        elif cmd.command == "wc":
            show_lines = True
            show_words = True
            show_chars = True

            if "-l" in cmd.args:
                show_lines, show_words, show_chars = True, False, False
            elif "-w" in cmd.args:
                show_lines, show_words, show_chars = False, True, False
            elif "-c" in cmd.args:
                show_lines, show_words, show_chars = False, False, True

            line_count = len(lines)
            word_count = sum(len(line.split()) for line in lines)
            char_count = len(pipe_input)

            result: list[str] = []
            if show_lines:
                result.append(f"{line_count:8}")
            if show_words:
                result.append(f"{word_count:8}")
            if show_chars:
                result.append(f"{char_count:8}")

            output.write_stdout(" ".join(result) + "\n")

        elif cmd.command == "sort":
            reverse = "-r" in cmd.args
            try:
                sorted_lines = sorted(lines, reverse=reverse)
                for line in sorted_lines:
                    output.write_stdout(f"{line}\n")
            except Exception as e:
                output.write_stderr(f"sort: {e}\n")

        elif cmd.command == "cut":
            # Simple cut implementation for piped input
            if "-f" in cmd.args:
                try:
                    field_idx = cmd.args.index("-f")
                    if field_idx + 1 < len(cmd.args):
                        field_spec = cmd.args[field_idx + 1]
                        field_num = int(field_spec) - 1  # Convert to 0-based

                        delimiter = None
                        if "-d" in cmd.args:
                            delim_idx = cmd.args.index("-d")
                            if delim_idx + 1 < len(cmd.args):
                                delimiter = cmd.args[delim_idx + 1]

                        for line in lines:
                            if delimiter:
                                fields = line.split(delimiter)
                            else:
                                fields = line.split()

                            if 0 <= field_num < len(fields):
                                output.write_stdout(f"{fields[field_num]}\n")
                except (ValueError, IndexError):
                    output.write_stderr("cut: invalid field specification\n")
            else:
                output.write_stderr(
                    "cut: field specification required for piped input\n"
                )

    def _write_to_file(self, filename: str, content: str, append: bool = False) -> None:
        """Write content to a file using Pebble.

        Args:
            filename: Target filename
            content: Content to write
            append: Whether to append to existing file
        """
        try:
            file_path = resolve_path(
                self._shell.current_directory, filename, self._shell.home_dir
            )

            if append:
                try:
                    with self.client.pull(file_path) as existing_file:
                        existing_content = existing_file.read()
                        if isinstance(existing_content, bytes):
                            existing_content = existing_content.decode("utf-8")

                    content = existing_content + content
                except (ops.pebble.PathError, FileNotFoundError):
                    # File doesn't exist, create new
                    pass

            self.client.push(file_path, content.encode("utf-8"), make_dirs=True)

        except Exception as e:
            print(f"Error writing to {filename}: {e}", file=sys.stderr)

    def _read_from_file(self, filename: str) -> str:
        """Read content from a file using Pebble.

        Args:
            filename: Source filename

        Returns:
            File content as string
        """
        try:
            file_path = resolve_path(
                self._shell.current_directory, filename, self._shell.home_dir
            )

            with self.client.pull(file_path) as file:
                content = file.read()
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                return content

        except Exception as e:
            print(f"Error reading from {filename}: {e}", file=sys.stderr)
            return ""

    def _show_help(self, output: CommandOutput, group: str | None = None):
        """Show help information with rich formatting and gaps between groups. If group is given, only show that group (case-insensitive, partial match)."""
        from .theme import get_theme

        theme = get_theme()

        # Group commands by category.
        categories: dict[str, list[tuple[str, str]]] = {}

        for cmd_name, cmd_obj in self.commands.items():
            try:
                category = cmd_obj.category
                help_text = cmd_obj.help
                if category not in categories:
                    categories[category] = []
                categories[category].append((cmd_name, help_text))
            except NotImplementedError:  # noqa: PERF203
                category = "Other"
                if category not in categories:
                    categories[category] = []
                categories[category].append(
                    (cmd_name, f"{cmd_name} - (help not available)")
                )

        # Define the order of categories:
        category_order = [
            "Filesystem Commands",
            "System Commands",
            "Network Commands",
            "Built-in Commands",
            "File Operations",
            "Remote Execution",
            "Pebble Management",
            "Shell Features",
            "Other",
        ]

        help_tables: list[Table | Text] = []
        if group:
            group_lower = group.lower()
            matched = False
            for category in category_order + list(categories.keys()):
                if (
                    category.lower().startswith(group_lower)
                    or group_lower in category.lower()
                ) and category in categories:
                    table = Table(
                        title=category,
                        show_header=True,
                        header_style=theme.header,
                        box=None,
                        expand=False,
                    )
                    table.add_column("Command", style=theme.primary, no_wrap=True)
                    table.add_column("Description", style=theme.data)
                    for cmd_name, help_text in sorted(categories[category]):
                        table.add_row(cmd_name, help_text)
                    help_tables.append(table)
                    matched = True
                    break
            if not matched:
                output.write_stdout(
                    f"[red]No command group found matching '{group}'.[/red]\n"
                )
                return
        else:
            for category in category_order:
                if category in categories:
                    table = Table(
                        title=category,
                        show_header=True,
                        header_style=theme.header,
                        box=None,
                        expand=False,
                    )
                    table.add_column("Command", style=theme.primary, no_wrap=True)
                    table.add_column("Description", style=theme.data)
                    for cmd_name, help_text in sorted(categories[category]):
                        table.add_row(cmd_name, help_text)
                    help_tables.append(table)
                    help_tables.append(Text(""))  # Add a gap

            # Display any remaining categories not in the predefined order.
            for category, commands in categories.items():
                if category not in category_order:
                    table = Table(
                        title=category,
                        show_header=True,
                        header_style=theme.header,
                        box=None,
                        expand=False,
                    )
                    table.add_column("Command", style=theme.primary, no_wrap=True)
                    table.add_column("Description", style=theme.data)
                    for cmd_name, help_text in sorted(commands):
                        table.add_row(cmd_name, help_text)
                    help_tables.append(table)
                    help_tables.append(Text(""))  # Add a gap

            # General commands
            general_table = Table(
                title="General Commands",
                show_header=True,
                header_style=theme.header,
                box=None,
                expand=False,
            )
            general_table.add_column("Command", style=theme.primary, no_wrap=True)
            general_table.add_column("Description", style=theme.data)
            general_table.add_row("help", "Show this help")
            general_table.add_row("exit", "Exit the shell")
            help_tables.append(general_table)

            # Remove trailing gap if present
            if help_tables and isinstance(help_tables[-1], Text):
                help_tables = help_tables[:-1]

        if help_tables:
            group_obj = Group(*help_tables)
            panel = Panel(
                group_obj, title="[b]Available Commands[/b]", style="bold blue"
            )
            self._shell.console.print(panel)

    def _skip_to_next_group(
        self, commands: list[ParsedCommand], current_index: int
    ) -> int:
        """Skip to the next command group after && or ||."""
        i = current_index + 1
        while i < len(commands):
            # Look for the next command that starts a new group
            # (not part of the current pipe or redirection sequence)
            if commands[i].type in [
                CommandType.SIMPLE,
                CommandType.REDIRECT_OUT,
                CommandType.REDIRECT_APPEND,
                CommandType.REDIRECT_IN,
            ]:
                break
            i += 1
        return i
