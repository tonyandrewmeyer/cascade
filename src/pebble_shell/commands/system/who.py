"""Implementation of WhoCommand."""

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
    read_proc_status_field,
)
from ...utils.table_builder import create_standard_table
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer


class WhoCommand(Command):
    """Show logged in users."""

    name = "who"
    help = "Show logged in users"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute who command with rich table output."""
        if handle_help_flag(self, args):
            return 0
        table = create_standard_table()
        table.add_column("USER", style="cyan", no_wrap=True)
        table.add_column("TTY", style="white", no_wrap=True)
        table.add_column("FROM", style="white", no_wrap=True)
        table.add_column("LOGIN@", style="white", no_wrap=True)
        table.add_column("IDLE", style="white", no_wrap=True)
        table.add_column("JCPU", style="white", no_wrap=True)
        table.add_column("PCPU", style="white", no_wrap=True)
        table.add_column("WHAT", style="green", no_wrap=False)

        proc_dirs: list[str] = []
        files = client.list_files("/proc")
        proc_dirs = [file_info.name for file_info in files if file_info.name.isdigit()]

        sessions: set[str] = set()
        for pid in proc_dirs:
            try:
                cmdline = read_proc_cmdline(client, pid)

                try:
                    uid = read_proc_status_field(client, pid, "Uid")
                except ProcReadError:
                    uid = None

                session_indicators = [
                    "ssh",
                    "sshd",
                    "login",
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
                ]
                if cmdline and any(
                    indicator in cmdline.lower() for indicator in session_indicators
                ):
                    username = (
                        get_user_name_for_uid(client, uid) or f"uid{uid}"
                        if uid
                        else "unknown"
                    )
                    tty = self._get_tty_info(client, pid)
                    session_id = f"{username}:{tty}:{cmdline[:20]}"
                    if session_id not in sessions:
                        sessions.add(session_id)
                        login_time = self._get_process_start_time(client, pid)
                        # For now, FROM, IDLE, JCPU, PCPU are not implemented (show as '-')
                        table.add_row(
                            f"[cyan]{username}[/cyan]",
                            tty,
                            "-",
                            login_time,
                            "-",
                            "-",
                            "-",
                            f"[green]{cmdline[:30]}[/green]",
                        )
            except Exception:  # noqa: S112, PERF203  # needed for process scanning
                continue

        if not sessions:
            self.console.print(
                Panel(
                    Text("No user sessions found", style="yellow"),
                    title="[b]who[/b]",
                    style="bold magenta",
                )
            )
            return 1
        self.console.print(table.build())
        return 0

    def _get_tty_info(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get TTY information for a process."""
        try:
            return get_process_tty(client, pid)
        except ProcReadError:
            return "?"

    def _get_process_start_time(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, pid: str
    ) -> str:
        """Get process start time (simplified)."""
        with client.pull(f"/proc/{pid}/stat") as file:
            stat_content = file.read()
        assert isinstance(stat_content, str)
        # Parse stat file (starttime is the 22nd field).
        parts = stat_content.strip().split()
        if len(parts) >= 22:
            return parts[21]
        return "unknown"
