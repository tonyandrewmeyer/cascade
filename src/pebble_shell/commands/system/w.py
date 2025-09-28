"""Implementation of WCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    get_process_tty,
    get_user_name_for_uid,
    read_proc_cmdline,
    read_proc_file,
    read_proc_status_fields,
)
from ...utils.table_builder import create_enhanced_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class WCommand(Command):
    """Show who is logged in and what they are doing."""

    name = "w"
    help = "Show who is logged in and what they are doing"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute w command."""
        if handle_help_flag(self, args):
            return 0
        try:
            # Get all processes
            proc_entries = client.list_files("/proc")
            pids = [entry.name for entry in proc_entries if entry.name.isdigit()]

            sessions: list[dict[str, str]] = []

            for pid in pids:
                try:
                    # Read process status fields
                    status_fields = read_proc_status_fields(
                        client, pid, ["Uid", "Name"]
                    )
                    uid = status_fields.get("Uid")
                    name = status_fields.get("Name")

                    # Read command line
                    cmdline = read_proc_cmdline(client, pid)
                    if cmdline == "unknown":
                        cmdline = ""

                    # Check if this is a login session
                    session_indicators = [
                        "bash",
                        "sh",
                        "zsh",
                        "fish",
                        "dash",
                        "ash",
                        "ksh",
                        "csh",
                        "tcsh",
                        "screen",
                        "tmux",
                        "login",
                        "sshd",
                    ]

                    if name and any(
                        indicator in name.lower() for indicator in session_indicators
                    ):
                        if uid:
                            username = get_user_name_for_uid(client, uid) or f"uid{uid}"
                        else:
                            username = "unknown"

                        tty = self._get_tty_for_process(client, pid)
                        start_time = self._get_process_start_time(client, pid)

                        sessions.append(
                            {
                                "user": username,
                                "tty": tty,
                                "from": "-",
                                "login": start_time,
                                "idle": "-",
                                "jcpu": "-",
                                "pcpu": "-",
                                "what": cmdline[:30] if cmdline else name,
                            }
                        )

                except Exception:  # noqa: PERF203, S112
                    continue

            if not sessions:
                self.console.print(
                    Panel(
                        Text("No active sessions found", style="yellow"),
                        title="[b]w[/b]",
                        style="bold magenta",
                    )
                )
                return 1

            # Display sessions
            table = create_enhanced_table()
            table.add_column("USER", style="cyan", no_wrap=True)
            table.add_column("TTY", style="green", no_wrap=True)
            table.add_column("FROM", style="yellow", no_wrap=True)
            table.add_column("LOGIN@", style="blue", no_wrap=True)
            table.add_column("IDLE", style="magenta", no_wrap=True)
            table.add_column("JCPU", style="white", no_wrap=True)
            table.add_column("PCPU", style="white", no_wrap=True)
            table.add_column("WHAT", style="green", no_wrap=False)

            for session in sessions:
                table.add_row(
                    session["user"],
                    session["tty"],
                    session["from"],
                    session["login"],
                    session["idle"],
                    session["jcpu"],
                    session["pcpu"],
                    session["what"],
                )

            self.console.print(table.build())

        except Exception as e:
            self.console.print(f"Error getting session information: {e}")
            return 1

        return 0

    def _get_tty_for_process(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get TTY for a process."""
        try:
            return get_process_tty(client, pid)
        except ProcReadError:
            return "?"

    def _get_process_start_time(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get process start time."""
        try:
            stat_content = read_proc_file(client, f"/proc/{pid}/stat")
            parts = stat_content.strip().split()
            if len(parts) >= 22:
                return parts[21]
            return "unknown"
        except (ProcReadError, ValueError, IndexError):
            return "unknown"
