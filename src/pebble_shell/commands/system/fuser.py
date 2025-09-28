"""Implementation of FuserCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer


class FuserCommand(Command):
    """Implementation of fuser command."""

    name = "fuser"
    help = "Show processes using files or sockets"
    category = "System"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the fuser command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        kill_processes = False
        interactive = False
        verbose = False
        files = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg == "-k" or arg == "--kill":
                kill_processes = True
            elif arg == "-i" or arg == "--interactive":
                interactive = True
            elif arg == "-v" or arg == "--verbose":
                verbose = True
            elif arg.startswith("-"):
                # Combined flags like -kv
                if "k" in arg:
                    kill_processes = True
                if "i" in arg:
                    interactive = True
                if "v" in arg:
                    verbose = True
            else:
                files.append(arg)
            i += 1

        if not files:
            self.console.print("[red]fuser: no files specified[/red]")
            return 1

        try:
            results = []

            for file_path in files:
                # Find processes using this file
                using_processes = []

                # Alternative: scan common process info
                for pid in range(1, 32768):  # Common PID range
                    try:
                        # Check if process exists and uses the file

                        # Try to read file descriptors
                        try:
                            with client.pull(
                                f"/proc/{pid}/cmdline", encoding="utf-8"
                            ) as f:
                                cmdline = f.read().strip()
                                if not cmdline:
                                    continue

                            # Check if this process might be using the file
                            # This is a simplified check - real fuser would check file descriptors
                            if file_path in cmdline:
                                proc_info = {
                                    "pid": pid,
                                    "cmdline": cmdline.replace("\0", " "),
                                }
                                using_processes.append(proc_info)

                        except ops.pebble.PathError:
                            continue

                    except Exception:  # noqa: S112
                        # Broad exception needed when scanning /proc - many different failure modes
                        continue

                # Also check /proc/mounts for filesystem usage
                if file_path.startswith("/"):
                    try:
                        with client.pull("/proc/mounts", encoding="utf-8") as f:
                            mount_content = f.read()
                            for line in mount_content.splitlines():
                                parts = line.strip().split()
                                if len(parts) >= 2 and (
                                    parts[0] == file_path or parts[1] == file_path
                                ):
                                    # This is a mounted filesystem, many processes likely use it
                                    # For simplicity, we'll note this but not list all processes
                                    break
                    except ops.pebble.PathError:
                        pass

                if using_processes:
                    results.append((file_path, using_processes))

            # Display results
            for file_path, processes in results:
                if verbose:
                    self.console.print(f"[bold]{file_path}:[/bold]")
                    for proc in processes:
                        self.console.print(f"  {proc['pid']}: {proc['cmdline']}")
                else:
                    pids = [str(proc["pid"]) for proc in processes]
                    self.console.print(f"{file_path}: {' '.join(pids)}")

                # Kill processes if requested
                if kill_processes:
                    for proc in processes:
                        pid = proc["pid"]
                        if interactive:
                            response = input(
                                f"Kill process {pid} ({proc['cmdline']})? (y/N): "
                            )
                            if response.lower() != "y":
                                continue

                        # Note: We can't actually kill processes through Pebble
                        # This is a limitation of the filesystem-only access
                        self.console.print(
                            f"[yellow]Cannot kill process {pid}: not supported with filesystem-only access[/yellow]"
                        )

            if not results:
                # No processes found, but this might not be an error
                # fuser often returns 1 when no processes are found
                return 1

            return 0

        except Exception as e:
            self.console.print(f"[red]fuser: {e}[/red]")
            return 1
