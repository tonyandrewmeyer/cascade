"""Remote command execution using Pebble's exec API."""

from __future__ import annotations

import sys
import time
from typing import TYPE_CHECKING, Any, Union

import ops

from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ExecCommand(Command):
    """Execute commands remotely using Pebble's exec API."""

    name = "exec"
    help = "Execute commands remotely"
    category = "Remote Execution"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute exec command."""
        if "--help" in args:
            self.show_help()
            return 0

        if not args:
            self.console.print("Usage: exec <command> [args...]")
            self.console.print("       exec -i <command>  # Interactive mode")
            self.console.print("       exec -d <command>  # Detached mode")
            self.console.print("Examples:")
            self.console.print("  exec ps aux")
            self.console.print("  exec -i /bin/bash")
            self.console.print("  exec python3 -c 'print(\"Hello\")'")
            return 0

        # Pre-process args to extract environment variables (-eVAR=value):
        environment: dict[str, str] = {}
        filtered_args = []
        for arg in args:
            if arg.startswith("-e") and "=" in arg:
                env_var = arg[2:]  # Remove -e
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    environment[key] = value
            else:
                filtered_args.append(arg)

        # Parse flags and options:
        valid_flags = {"i": bool, "d": bool, "w": str, "u": str, "g": str}
        result = parse_flags(filtered_args, valid_flags, self.shell)
        if result is None:
            return 1
        flags, remaining_args = result

        interactive = flags.get("i", False)
        detached = flags.get("d", False)
        working_dir = flags.get("w")
        user = flags.get("u")
        group = flags.get("g")

        command_args = remaining_args

        if not command_args:
            self.console.print("exec: no command specified")
            return 1

        return self.execute_remote_command(
            client,
            command_args,
            interactive=interactive,
            detached=detached,
            environment=environment or None,
            working_dir=working_dir,
            user=user,
            group=group,
        )

    def execute_remote_command(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        cmd: list[str],
        interactive: bool = False,
        detached: bool = False,
        environment: dict[str, str] | None = None,
        working_dir: str | None = None,
        user: str | None = None,
        group: str | None = None,
    ):
        """Execute command using Pebble's exec API."""
        # Build exec options
        exec_options: dict[str, Any] = {}
        if environment:
            exec_options["environment"] = environment
        # TODO: is there some way to have a "working_dir" with Pebble?
        if user:
            exec_options["user"] = user
        if group:
            exec_options["group"] = group

        if interactive:
            # Interactive mode - enable streaming I/O
            self.console.print(f"Starting interactive session: {' '.join(cmd)}")
            self.console.print("Type 'exit' or Ctrl+D to end the session.")
            self.console.print("-" * 50)

            # Enable streaming for interactive mode with actual stdin/stdout/stderr
            exec_options["stdin"] = sys.stdin
            exec_options["stdout"] = sys.stdout
            exec_options["stderr"] = sys.stderr

            # Execute with streaming I/O
            process = client.exec(cmd, **exec_options)

            try:
                # Wait for the process to complete
                process.wait()
                return 0
            except ops.pebble.ExecError as e:
                self.console.print(f"\nProcess exited with code: {e.exit_code}")
                return e.exit_code
            except KeyboardInterrupt:
                self.console.print("\nInterrupted")
                process.send_signal("SIGTERM")
                time.sleep(0.1)
                process.send_signal("SIGKILL")
                return 0
            finally:
                self.console.print("\nInteractive session ended.")

        elif detached:
            # Detached mode - start and return immediately.
            exec_options["stdin"] = None
            exec_options["stdout"] = None
            exec_options["stderr"] = None
            process = client.exec(cmd, **exec_options)
            self.console.print(f"Started detached process: {' '.join(cmd)}")
            return 0
        else:
            # Normal mode - capture and display output.
            try:
                process = client.exec(cmd)
                stdout, stderr = process.wait_output()
                if stdout:
                    self.console.print(stdout, end="")
                if stderr:
                    self.shell.error_console.print(stderr, end="")
                return 0
            except ops.pebble.ExecError as e:
                self.console.print(f"Command failed: {e}")
                if hasattr(e, "stdout") and e.stdout:
                    self.console.print(e.stdout, end="")
                if hasattr(e, "stderr") and e.stderr:
                    self.shell.error_console.print(e.stderr, end="")
                return e.exit_code
            except ops.pebble.APIError as e:
                self.console.print(f"Command failed: {e}")
                return 1
