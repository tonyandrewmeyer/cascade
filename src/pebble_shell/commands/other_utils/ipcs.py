"""Implementation of IpcsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the system category.
class IpcsCommand(Command):
    """Implementation of ipcs command."""

    name = "ipcs"
    help = "Display information on IPC facilities"
    category = "System Info"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the ipcs command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        result = parse_flags(
            args,
            {
                "m": bool,  # shared memory
                "q": bool,  # message queues
                "s": bool,  # semaphores
                "a": bool,  # all
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        show_shm = flags.get("m", False)
        show_msg = flags.get("q", False)
        show_sem = flags.get("s", False)
        show_all = flags.get("a", False) or not (show_shm or show_msg or show_sem)

        try:
            displayed_any = False

            if (show_all or show_shm) and self._show_shared_memory(client):
                displayed_any = True

            if show_all or show_msg:
                if displayed_any:
                    self.console.print()
                if self._show_message_queues(client):
                    displayed_any = True

            if show_all or show_sem:
                if displayed_any:
                    self.console.print()
                if self._show_semaphores(client):
                    displayed_any = True

            return 0

        except Exception as e:
            self.console.print(f"[red]ipcs: {e}[/red]")
            return 1

    def _show_shared_memory(self, client: ClientType) -> bool:
        """Show shared memory segments."""
        self.console.print("[bold]------ Shared Memory Segments --------[/bold]")
        self.console.print(
            "key        shmid      owner      perms      bytes      nattch     status"
        )

        shm_info = safe_read_file(client, "/proc/sysvipc/shm", self.shell)
        if shm_info:
            lines = shm_info.strip().split("\n")[1:]  # Skip header
            if lines and lines[0].strip():
                for line in lines:
                    if line.strip():
                        fields = line.split()
                        if len(fields) >= 6:
                            key = fields[0]
                            shmid = fields[1]
                            owner = "root"  # Simplified
                            perms = fields[2]
                            size = fields[3]
                            nattch = fields[4]
                            status = ""
                            self.console.print(
                                f"{key:10} {shmid:10} {owner:10} {perms:10} {size:10} {nattch:10} {status}"
                            )
            else:
                self.console.print("(no shared memory segments)")
        else:
            self.console.print("(no shared memory segments)")

        return True

    def _show_message_queues(self, client: ClientType) -> bool:
        """Show message queues."""
        self.console.print("[bold]------ Message Queues --------[/bold]")
        self.console.print(
            "key        msqid      owner      perms      used-bytes   messages"
        )

        msg_info = safe_read_file(client, "/proc/sysvipc/msg", self.shell)
        if msg_info:
            lines = msg_info.strip().split("\n")[1:]  # Skip header
            if lines and lines[0].strip():
                for line in lines:
                    if line.strip():
                        fields = line.split()
                        if len(fields) >= 6:
                            key = fields[0]
                            msqid = fields[1]
                            owner = "root"  # Simplified
                            perms = fields[2]
                            cbytes = fields[3]
                            qnum = fields[4]
                            self.console.print(
                                f"{key:10} {msqid:10} {owner:10} {perms:10} {cbytes:12} {qnum:8}"
                            )
            else:
                self.console.print("(no message queues)")
        else:
            self.console.print("(no message queues)")

        return True

    def _show_semaphores(self, client: ClientType) -> bool:
        """Show semaphore arrays."""
        self.console.print("[bold]------ Semaphore Arrays --------[/bold]")
        self.console.print("key        semid      owner      perms      nsems")

        sem_info = safe_read_file(client, "/proc/sysvipc/sem", self.shell)
        if sem_info:
            lines = sem_info.strip().split("\n")[1:]  # Skip header
            if lines and lines[0].strip():
                for line in lines:
                    if line.strip():
                        fields = line.split()
                        if len(fields) >= 5:
                            key = fields[0]
                            semid = fields[1]
                            owner = "root"  # Simplified
                            perms = fields[2]
                            nsems = fields[3]
                            self.console.print(
                                f"{key:10} {semid:10} {owner:10} {perms:10} {nsems:5}"
                            )
            else:
                self.console.print("(no semaphore arrays)")
        else:
            self.console.print("(no semaphore arrays)")

        return True
