"""Implementation of PidofCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.proc_reader import (
    read_proc_file,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PidofCommand(Command):
    """Implementation of pidof command."""

    name = "pidof"
    help = "Find process IDs by name"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Find process IDs by name.

Usage: pidof [OPTIONS] PROGRAM [PROGRAM...]

Description:
    Find the process ID(s) of running programs.

Options:
    -s              Single shot - return only one PID
    -c              Only return PIDs for running programs
    -x              Include shell scripts
    -o PID          Omit processes with given PID
    -h, --help      Show this help message

Examples:
    pidof sshd
    pidof -s nginx
    pidof python bash
    pidof -x script.sh
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the pidof command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "s": bool,  # single shot
                "c": bool,  # only running
                "x": bool,  # include scripts
                "o": int,  # omit PID
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        single_shot = flags.get("s", False)
        only_running = flags.get("c", False)
        include_scripts = flags.get("x", False)
        omit_pid = flags.get("o")

        if not positional_args:
            self.console.print("[red]pidof: missing program name[/red]")
            return 1

        program_names = positional_args
        found_pids = []

        try:
            # Read process list from /proc
            try:
                proc_dirs = client.list_files("/proc")
                proc_pids = [d.name for d in proc_dirs if d.name.isdigit()]
            except ops.pebble.PathError:
                self.console.print("[red]pidof: cannot access /proc[/red]")
                return 1

            # Check each process
            for pid in proc_pids:
                if omit_pid and int(pid) == omit_pid:
                    continue

                try:
                    # Read process command line
                    comm_content = read_proc_file(client, f"/proc/{pid}/comm")
                    comm = comm_content.strip()

                    # Also check cmdline for scripts if requested
                    if include_scripts:
                        try:
                            cmdline_content = read_proc_file(
                                client, f"/proc/{pid}/cmdline"
                            )
                            cmdline = cmdline_content.replace("\0", " ").strip()
                        except ops.pebble.PathError:
                            cmdline = ""
                    else:
                        cmdline = ""

                    # Check if process matches any of the program names
                    for program_name in program_names:
                        if comm == program_name or (
                            include_scripts and program_name in cmdline
                        ):
                            # Check if process is running if requested
                            if only_running:
                                try:
                                    stat_content = read_proc_file(
                                        client, f"/proc/{pid}/stat"
                                    )
                                    stat_data = stat_content.split()
                                    if len(stat_data) > 2 and stat_data[2] not in [
                                        "R",
                                        "S",
                                    ]:
                                        continue  # Skip non-running processes
                                except ops.pebble.PathError:
                                    continue

                            found_pids.append(int(pid))

                            if single_shot:
                                break

                except ops.pebble.PathError:
                    continue  # Process disappeared or inaccessible

                if single_shot and found_pids:
                    break

            # Output results
            if found_pids:
                if single_shot:
                    self.console.print(str(found_pids[0]))
                else:
                    self.console.print(" ".join(map(str, sorted(found_pids))))
                return 0
            else:
                return 1  # No processes found

        except Exception as e:
            self.console.print(f"[red]pidof: {e}[/red]")
            return 1
