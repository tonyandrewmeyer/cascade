"""Implementation of dnsdomainname command."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from ...utils.command_helpers import handle_help_flag, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import ops
    import shimmer

    from pebble_shell.shell import PebbleShell

# TODO: Use the prototype from Shimmer.
ClientType = Union["ops.pebble.Client", "shimmer.PebbleCliClient"]


class DnsdomainnameCommand(Command):
    """Implementation of dnsdomainname command."""

    name = "dnsdomainname"
    help = "Display the system's DNS domain name"
    category = "Network"

    def show_help(self):
        """Show command help."""
        help_text = """Display the system's DNS domain name.

Usage: dnsdomainname [OPTIONS]

Description:
    Display the DNS domain name of the system if available.

Options:
    -h, --help      Show this help message

Examples:
    dnsdomainname   # Show DNS domain name
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dnsdomainname command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Try to get domain name from /etc/resolv.conf
            try:
                resolv_conf = safe_read_file(client, "/etc/resolv.conf", self.shell)
                if resolv_conf:
                    for line in resolv_conf.split("\n"):
                        line = line.strip()
                        if line.startswith("search ") or line.startswith("domain "):
                            domain = line.split()[1] if len(line.split()) > 1 else ""
                            if domain:
                                self.console.print(domain)
                                return 0
            except Exception:  # noqa: S110
                # Broad exception needed for DNS configuration probing
                pass

            # Try to get from hostname -f equivalent
            try:
                hostname_content = safe_read_file(client, "/etc/hostname", self.shell)
                if hostname_content:
                    hostname = hostname_content.strip()
                    if "." in hostname:
                        domain = ".".join(hostname.split(".")[1:])
                        if domain:
                            self.console.print(domain)
                            return 0
            except Exception:  # noqa: S110
                # Broad exception needed for DNS configuration probing
                pass

            # Fallback - try /proc/sys/kernel/domainname
            try:
                domainname = safe_read_file(
                    client, "/proc/sys/kernel/domainname", self.shell
                )
                if domainname and domainname.strip() != "(none)":
                    self.console.print(domainname.strip())
                    return 0
            except Exception:  # noqa: S110
                # Broad exception needed for DNS configuration probing
                pass

            # No domain name found
            self.console.print("[yellow]dnsdomainname: no domain name found[/yellow]")
            return 1

        except Exception as e:
            self.console.print(f"[red]dnsdomainname: {e}[/red]")
            return 1
