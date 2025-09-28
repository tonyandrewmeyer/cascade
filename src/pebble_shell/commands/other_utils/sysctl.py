"""Implementation of SysctlCommand."""

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
class SysctlCommand(Command):
    """Implementation of sysctl command (read-only)."""

    name = "sysctl"
    help = "Display kernel parameters"
    category = "System Info"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the sysctl command."""
        if handle_help_flag(self, args):
            return 0

        result = parse_flags(
            args,
            {
                "a": bool,  # all
                "all": bool,
                "n": bool,  # no names
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        show_all = flags.get("a", False) or flags.get("all", False)
        no_names = flags.get("n", False)
        parameters = positional_args

        try:
            if show_all:
                return self._show_all_parameters(client, no_names)
            elif parameters:
                return self._show_specific_parameters(client, parameters, no_names)
            else:
                self.console.print("[red]sysctl: no parameters specified[/red]")
                return 1

        except Exception as e:
            self.console.print(f"[red]sysctl: {e}[/red]")
            return 1

    def _show_all_parameters(self, client: ClientType, no_names: bool) -> int:
        """Show all available parameters."""
        try:
            # Read from /proc/sys hierarchy
            common_params = [
                ("kernel.hostname", "/proc/sys/kernel/hostname"),
                ("kernel.ostype", "/proc/sys/kernel/ostype"),
                ("kernel.osrelease", "/proc/sys/kernel/osrelease"),
                ("kernel.version", "/proc/sys/kernel/version"),
                ("vm.swappiness", "/proc/sys/vm/swappiness"),
                ("net.ipv4.ip_forward", "/proc/sys/net/ipv4/ip_forward"),
                (
                    "net.ipv4.tcp_keepalive_time",
                    "/proc/sys/net/ipv4/tcp_keepalive_time",
                ),
                ("fs.file-max", "/proc/sys/fs/file-max"),
            ]

            found_any = False
            for param_name, proc_path in common_params:
                value = safe_read_file(client, proc_path, self.shell)
                if value is not None:
                    value = value.strip()
                    if no_names:
                        self.console.print(value)
                    else:
                        self.console.print(f"{param_name} = {value}")
                    found_any = True

            if not found_any:
                self.console.print("[yellow]sysctl: no parameters found[/yellow]")
                return 1

            return 0

        except Exception as e:
            self.console.print(f"[red]sysctl: error reading parameters: {e}[/red]")
            return 1

    def _show_specific_parameters(
        self, client: ClientType, parameters: list[str], no_names: bool
    ) -> int:
        """Show specific parameters."""
        param_map = {
            "kernel.hostname": "/proc/sys/kernel/hostname",
            "kernel.ostype": "/proc/sys/kernel/ostype",
            "kernel.osrelease": "/proc/sys/kernel/osrelease",
            "kernel.version": "/proc/sys/kernel/version",
            "vm.swappiness": "/proc/sys/vm/swappiness",
            "net.ipv4.ip_forward": "/proc/sys/net/ipv4/ip_forward",
            "net.ipv4.tcp_keepalive_time": "/proc/sys/net/ipv4/tcp_keepalive_time",
            "fs.file-max": "/proc/sys/fs/file-max",
        }

        exit_code = 0
        for param in parameters:
            if param in param_map:
                try:
                    value = safe_read_file(client, param_map[param], self.shell)
                    if value is not None:
                        value = value.strip()
                        if no_names:
                            self.console.print(value)
                        else:
                            self.console.print(f"{param} = {value}")
                    else:
                        self.console.print(
                            f"[red]sysctl: cannot read parameter '{param}'[/red]"
                        )
                        exit_code = 1
                except Exception:
                    self.console.print(
                        f"[red]sysctl: cannot read parameter '{param}'[/red]"
                    )
                    exit_code = 1
            else:
                # Try to convert parameter name to proc path
                proc_path = "/proc/sys/" + param.replace(".", "/")
                try:
                    value = safe_read_file(client, proc_path, self.shell)
                    if value is not None:
                        value = value.strip()
                        if no_names:
                            self.console.print(value)
                        else:
                            self.console.print(f"{param} = {value}")
                    else:
                        self.console.print(
                            f"[red]sysctl: cannot read parameter '{param}'[/red]"
                        )
                        exit_code = 1
                except Exception:
                    self.console.print(
                        f"[red]sysctl: unknown parameter '{param}'[/red]"
                    )
                    exit_code = 1

        return exit_code
