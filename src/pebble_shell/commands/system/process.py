"""Implementation of ProcessCommand."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    get_process_tty,
    get_user_name_for_uid,
    parse_proc_stat,
    read_proc_cmdline,
    read_proc_environ,
    read_proc_file,
    read_proc_status_fields,
)
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class ProcessCommand(Command):
    """Show process information."""

    name = "ps"
    help = "Show running processes (supports -aux, e, eww for environment)"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute ps command with rich table output."""
        if handle_help_flag(self, args):
            return 0
        # Parse flags
        show_all = False
        user_format = False
        show_no_tty = False
        show_env = False
        show_full_env = False

        # Handle -aux as a special case
        if "-aux" in args:
            show_all = True
            user_format = True
            show_no_tty = True
            args = [arg for arg in args if arg != "-aux"]

        # Handle aux as a special case (without dash)
        if "aux" in args:
            show_all = True
            user_format = True
            show_no_tty = True
            args = [arg for arg in args if arg != "aux"]

        # Parse individual flags (including 'e' for environment)
        remaining_args = []
        for arg in args:
            if arg.startswith("-"):
                # Handle combined flags like -aux, -ae, etc.
                flags = arg[1:]
                if "a" in flags:
                    show_all = True
                if "u" in flags:
                    user_format = True
                if "x" in flags:
                    show_no_tty = True
                if "e" in flags:
                    show_env = True
            elif arg == "e":
                # Single 'e' flag without dash
                show_env = True
            elif arg == "eww":
                # 'eww' shows full environment
                show_env = True
                show_full_env = True
            else:
                remaining_args.append(arg)

        args = remaining_args

        proc_dirs: list[str] = []
        files = client.list_files("/proc")
        proc_dirs = [file_info.name for file_info in files if file_info.name.isdigit()]
        if not proc_dirs:
            self.console.print(
                Panel("No process information found", style="bold yellow")
            )
            return 1

        # Create table based on flags
        if user_format:
            table = create_enhanced_table()
            table.add_column("USER", style="cyan", no_wrap=True)
            table.add_column("PID", style="cyan", no_wrap=True)
            table.add_column("%CPU", style="yellow", justify="right")
            table.add_column("%MEM", style="yellow", justify="right")
            table.add_column("VSZ", style="white", justify="right")
            table.add_column("RSS", style="white", justify="right")
            table.add_column("TTY", style="white", no_wrap=True)
            table.add_column("STAT", style="white", no_wrap=True)
            table.add_column("START", style="white", no_wrap=True)
            table.add_column("TIME", style="white", no_wrap=True)
            table.add_column("COMMAND", style="green")
        else:
            table = create_enhanced_table()
            table.add_column("PID", style="cyan", no_wrap=True)
            table.add_column("CMD", style="green")

        for pid in sorted(proc_dirs, key=int):
            cmdline = read_proc_cmdline(client, pid)
            if cmdline == "unknown":
                try:
                    comm = read_proc_file(client, f"/proc/{pid}/comm")
                    cmdline = f"[{comm.strip()}]"
                except ProcReadError:
                    continue

            # Add environment variables if requested
            if show_env:
                env_str = self._format_environment(client, pid, show_full_env)
                if env_str:
                    cmdline = f"{cmdline} {env_str}"

            # Get status info for user format
            if user_format:
                status_info = self._get_process_status(client, pid)
                if status_info is None:
                    continue

                # Apply filters
                if not show_all and not show_no_tty and status_info["tty"] == "?":
                    continue
                if show_no_tty and not show_all and status_info["tty"] != "?":
                    continue

                # Truncate command if too long
                if len(cmdline) > 30:
                    cmdline = cmdline[:27] + "..."

                # Use Text objects to avoid Rich markup interpretation issues
                from rich.text import Text

                table.add_row(
                    Text(status_info["user"], style="cyan"),
                    Text(pid, style="cyan"),
                    Text(f"{status_info['cpu_percent']:.1f}", style="yellow"),
                    Text(f"{status_info['mem_percent']:.1f}", style="yellow"),
                    Text(str(status_info.get("vsz", "?")), style="white"),
                    Text(str(status_info.get("rss", "?")), style="white"),
                    status_info["tty"],
                    status_info["stat"],
                    status_info["start"],
                    status_info["time"],
                    Text(cmdline, style="green"),
                )
            else:
                # Simple format
                if len(cmdline) > 50:
                    cmdline = cmdline[:47] + "..."
                # Use Text objects to avoid Rich markup interpretation
                from rich.text import Text

                pid_text = Text(pid, style="cyan")
                cmd_text = Text(cmdline, style="green")
                table.add_row(pid_text, cmd_text)

        self.console.print(table.build())
        return 0

    def _get_process_status(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> dict[str, Any] | None:
        """Get detailed process status information."""
        status_info: dict[str, Any] = {}

        try:
            # Use proc_reader utilities for status fields
            status_fields = read_proc_status_fields(
                client, pid, ["Uid", "VmSize", "VmRSS"]
            )
            uid = status_fields.get("Uid")
            if uid:
                status_info["user"] = get_user_name_for_uid(client, uid) or f"uid{uid}"

            status_info["vsz"] = status_fields.get("VmSize", "?")
            status_info["rss"] = status_fields.get("VmRSS", "?")
        except ProcReadError:
            status_info["user"] = "unknown"
            status_info["vsz"] = "?"
            status_info["rss"] = "?"

        try:
            stat_content = read_proc_file(client, f"/proc/{pid}/stat")
            stat_parts = stat_content.strip().split()
        except ProcReadError:
            stat_parts = []
        if len(stat_parts) >= 22:
            status_info["stat"] = stat_parts[2]  # State
            start_time = int(stat_parts[21])
            # Convert to human readable start time (simplified)
            # Get system boot time from /proc/stat
            try:
                stat_data = parse_proc_stat(client)
                boot_time = stat_data.get("system", {}).get("btime", 0)

                # Calculate actual start time
                # start_time is in clock ticks since boot, convert to seconds
                clock_ticks_per_second = 100
                start_seconds = start_time / clock_ticks_per_second
                actual_start_time = boot_time + start_seconds

                # Format as readable time
                dt = datetime.datetime.fromtimestamp(actual_start_time)
                status_info["start"] = dt.strftime("%H:%M")
            except (ops.pebble.PathError, ValueError, IndexError):
                status_info["start"] = "?"

            # Calculate CPU time from utime and stime
            if len(stat_parts) >= 15:
                utime = int(stat_parts[13])  # User time in clock ticks
                stime = int(stat_parts[14])  # System time in clock ticks
                total_time = utime + stime

                # Convert clock ticks to seconds (assuming 100 Hz clock)
                clock_ticks_per_second = 100
                total_seconds = total_time / clock_ticks_per_second

                # Format as HH:MM:SS
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)

                if hours > 0:
                    status_info["time"] = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    status_info["time"] = f"{minutes:02d}:{seconds:02d}"
            else:
                status_info["time"] = "00:00"
        else:
            status_info["stat"] = "?"
            status_info["start"] = "?"
            status_info["time"] = "00:00"

        status_info["tty"] = self._get_tty_info(client, pid)

        status_info["cpu_percent"] = 0.0
        status_info["mem_percent"] = 0.0

        return status_info

    def _get_tty_info(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get TTY information for a process."""
        try:
            return get_process_tty(client, pid)
        except ProcReadError:
            return "?"

    def _format_environment(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str, full: bool
    ) -> str:
        """Format environment variables for display with command.

        Args:
            client: Pebble client
            pid: Process ID
            full: If True, show full environment (eww). If False, show abbreviated (e)

        Returns:
            Formatted environment string
        """
        try:
            env_vars = read_proc_environ(client, pid)
            if not env_vars:
                return ""

            # Format as KEY=VALUE pairs
            env_pairs = [f"{k}={v}" for k, v in env_vars.items()]

            if full:
                # Show full environment (eww)
                return " ".join(env_pairs)
            else:
                # Show abbreviated environment (e) - limit length
                env_str = " ".join(env_pairs)
                # Truncate if too long (similar to standard ps e behavior)
                max_len = 200
                if len(env_str) > max_len:
                    env_str = env_str[:max_len] + "..."
                return env_str

        except ProcReadError:
            return ""
