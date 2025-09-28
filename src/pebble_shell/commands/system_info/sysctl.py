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


class SysctlCommand(Command):
    """Implementation of sysctl command (read-only)."""

    name = "sysctl"
    help = "Display kernel parameters"
    category = "System Info"

    def show_help(self):
        """Show command help."""
        help_text = """Display kernel parameters.

Usage: sysctl [OPTIONS] [PARAMETER...]

Description:
    Display or modify kernel parameters. Read-only version in Cascade.

Options:
    -a, --all       Display all parameters
    -n              Don't print key names, only values
    -h, --help      Show this help message

Examples:
    sysctl -a                    # Show all parameters
    sysctl kernel.hostname       # Show specific parameter
    sysctl net.ipv4.ip_forward   # Show IP forwarding setting
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the sysctl command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "a": bool,  # all
                "all": bool,
                "n": bool,  # no names
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

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
                try:
                    value = safe_read_file(client, proc_path)
                    if value is not None:
                        value = value.strip()
                        if no_names:
                            self.console.print(value)
                        else:
                            self.console.print(f"{param_name} = {value}")
                        found_any = True
                except Exception:  # noqa: S112, PERF203  # needed for system parameter scanning
                    # Broad exception needed when scanning system parameters
                    continue

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
                    value = safe_read_file(client, param_map[param])
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
                    value = safe_read_file(client, proc_path)
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
