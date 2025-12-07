"""Implementation of ReadprofileCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ReadprofileCommand(Command):
    """Implementation of readprofile command."""

    name = "readprofile"
    help = "Display kernel profiling information"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display kernel profiling information.

Usage: readprofile [OPTIONS]

Description:
    Read and display kernel profiling information from /proc/profile.

Options:
    -m FILE         System.map file for symbol lookup
    -p FILE         Profile data file (default: /proc/profile)
    -M MULT         Profiling multiplier
    -i              Info about the profiling step
    -v              Verbose output
    -a              Print all symbols, even if count is 0
    -b              Print individual histogram buckets
    -s              Print individual histogram steps
    -n              Disable byte order auto-detection
    -r              Reset the profiling buffer
    -h, --help      Show this help message

Examples:
    readprofile         # Display kernel profile data
    readprofile -i      # Show profiling info
        """
        self.console.print(help_text)

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the readprofile command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "m": str,  # system.map file
                "p": str,  # profile file
                "M": str,  # multiplier
                "i": bool,  # info
                "v": bool,  # verbose
                "a": bool,  # all symbols
                "b": bool,  # buckets
                "s": bool,  # steps
                "n": bool,  # no auto-detection
                "r": bool,  # reset
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        profile_file = flags.get("p") or "/proc/profile"
        show_info = flags.get("i", False)
        verbose = flags.get("v", False)
        show_all = flags.get("a", False)
        reset_buffer = flags.get("r", False)

        try:
            if reset_buffer:
                self.console.print(
                    get_theme().warning_text(
                        "Cannot reset profiling buffer with filesystem-only access"
                    )
                )
                return 1

            if show_info:
                # Try to get profiling information
                try:
                    with client.pull(
                        "/proc/sys/kernel/prof_cpu_mask", encoding="utf-8"
                    ) as f:
                        cpu_mask = f.read().strip()
                        self.console.print(f"Profiling CPU mask: {cpu_mask}")
                except ops.pebble.PathError:
                    pass

                try:
                    with client.pull(
                        "/proc/sys/kernel/profiling", encoding="utf-8"
                    ) as f:
                        profiling = f.read().strip()
                        self.console.print(f"Profiling enabled: {profiling}")
                except ops.pebble.PathError:
                    pass

                self.console.print(f"Profile data file: {profile_file}")
                return 0

            # Try to read the profile data
            try:
                with client.pull(profile_file, encoding="utf-8") as f:
                    content = f.read()

                if not content.strip():
                    self.console.print(
                        get_theme().warning_text("No profiling data available")
                    )
                    return 0

                # Parse profiling data (this is typically binary, but we'll try to handle it)
                lines = content.splitlines()

                if verbose:
                    self.console.print(f"Reading profile data from {profile_file}")
                    self.console.print(f"Profile contains {len(lines)} entries")

                # Display profiling information
                self.console.print("  total                                      ticks")

                total_ticks = 0
                for line in lines:
                    line = line.strip()
                    if line:
                        # Try to parse profiling line
                        # Format varies, but typically shows function and tick count
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                ticks = int(parts[0])
                                function = " ".join(parts[1:])
                                if ticks > 0 or show_all:
                                    self.console.print(f"{ticks:6d} {function}")
                                    total_ticks += ticks
                            except ValueError:
                                if verbose:
                                    self.console.print(f"Unparsable line: {line}")

                self.console.print(f"{total_ticks:6d} total")
                return 0

            except ops.pebble.PathError:
                self.console.print(
                    get_theme().warning_text(
                        f"{profile_file} not accessible or profiling not enabled"
                    )
                )
                return 1

        except Exception as e:
            self.console.print(get_theme().error_text(f"readprofile: {e}"))
            return 1
