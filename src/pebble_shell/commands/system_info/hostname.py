"""Implementation of HostnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command
from .exceptions import SystemInfoError

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class HostnameCommand(Command):
    """Implementation of hostname command."""

    name = "hostname"
    help = "Display the system hostname"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display the system hostname.

Usage: hostname [OPTIONS]

Options:
    -h, --help      Show this help message
    -f, --fqdn      Display the fully qualified domain name
    -i, --ip        Display the IP address
    -I, --all-ip    Display all IP addresses
    -A, --all-fqdn  Display all FQDNs
    -s, --short     Display the short hostname
    -d, --domain    Display the domain name
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the hostname command."""
        self.client = client
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "f": bool,  # fully qualified domain name
                "s": bool,  # short hostname
                "d": bool,  # domain name
                "i": bool,  # IP address
                "I": bool,  # all IP addresses
                "A": bool,  # all FQDNs
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        fqdn = flags.get("f", False)
        short = flags.get("s", False)
        domain = flags.get("d", False)
        ip_address = flags.get("i", False)
        all_ips = flags.get("I", False)
        all_fqdns = flags.get("A", False)

        try:
            if ip_address or all_ips:
                return self._show_ip_addresses(all_ips)
            elif domain:
                return self._show_domain()
            elif all_fqdns:
                return self._show_all_fqdns()
            elif fqdn:
                return self._show_fqdn()
            elif short:
                return self._show_short_hostname()
            else:
                # Default behavior - show hostname
                return self._show_hostname()

        except SystemInfoError as e:
            self.console.print(get_theme().error_text(f"hostname: {e}"))
            return 1

    def _get_help_text(self) -> str:
        """Get help text for the hostname command."""
        return """
hostname - display or set system hostname

USAGE:
    hostname [OPTIONS]

OPTIONS:
    -f, --fqdn      Display fully qualified domain name
    -s, --short     Display short hostname (default)
    -d, --domain    Display domain name only
    -i, --ip-address Display IP address
    -I, --all-ip-addresses Display all IP addresses
    -A, --all-fqdns Display all FQDNs
    -h, --help      Show this help message

EXAMPLES:
    hostname        # Show hostname
    hostname -f     # Show FQDN
    hostname -i     # Show IP address
"""

    def _show_hostname(self) -> int:
        """Show the system hostname."""
        try:
            # Try to read hostname from /etc/hostname
            try:
                hostname_content = safe_read_file(self.client, "/etc/hostname")
                hostname = hostname_content.strip() if hostname_content else ""
                if hostname:
                    self.console.print(hostname)
                    return 0
            except ops.pebble.PathError:
                pass

            # Fallback: try to get hostname from /proc/sys/kernel/hostname
            try:
                with self.client.pull(
                    "/proc/sys/kernel/hostname", encoding="utf-8"
                ) as f:
                    hostname = f.read().strip()
                if hostname:
                    self.console.print(hostname)
                    return 0
            except ops.pebble.PathError:
                pass

            # Last resort: check uname for nodename
            hostname = self._get_uname_field("nodename")
            if hostname:
                self.console.print(hostname)
                return 0

            raise SystemInfoError("Cannot determine hostname")
        except Exception as e:
            raise SystemInfoError(f"Failed to get hostname: {e}") from e

    def _show_short_hostname(self) -> int:
        """Show short hostname."""
        try:
            hostname = self._get_hostname()
            short_name = hostname.split(".")[0]
            self.console.print(short_name)
            return 0
        except Exception as e:
            raise SystemInfoError(f"Failed to get short hostname: {e}") from e

    def _show_fqdn(self) -> int:
        """Show fully qualified domain name."""
        try:
            # Try to resolve FQDN using hostname and /etc/hosts
            hostname = self._get_hostname()

            # If hostname already contains dots, it might be FQDN
            if "." in hostname:
                self.console.print(hostname)
                return 0

            # Try to find FQDN in /etc/hosts
            try:
                hosts_content = safe_read_file(self.client, "/etc/hosts") or ""

                for line in hosts_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            for name in parts[1:]:
                                if name.startswith(hostname + "."):
                                    self.console.print(name)
                                    return 0
            except ops.pebble.PathError:
                pass

            # Fallback: just return hostname
            self.console.print(hostname)
            return 0
        except Exception as e:
            raise SystemInfoError(f"Failed to get FQDN: {e}") from e

    def _show_domain(self) -> int:
        """Show domain name only."""
        try:
            fqdn = self._get_hostname()
            parts = fqdn.split(".", 1)
            if len(parts) > 1:
                self.console.print(parts[1])
            else:
                self.console.print("")
            return 0
        except Exception as e:
            raise SystemInfoError(f"Failed to get domain: {e}") from e

    def _show_ip_addresses(self, show_all: bool) -> int:
        """Show IP address(es)."""
        try:
            # Read network interfaces from /proc/net/fib_trie or /proc/net/route
            # This is complex, so for now we'll use a simpler approach

            # Try to get IP from hostname resolution in /etc/hosts
            hostname = self._get_hostname()

            try:
                hosts_content = safe_read_file(self.client, "/etc/hosts") or ""

                ips = set()
                for line in hosts_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2 and hostname in parts[1:]:
                            ip = parts[0]
                            # Simple IP validation
                            if self._is_valid_ip(ip):
                                ips.add(ip)

                if ips:
                    if show_all:
                        for ip in sorted(ips):
                            self.console.print(ip)
                    else:
                        # Show first non-localhost IP
                        for ip in sorted(ips):
                            if ip != "127.0.0.1" and ip != "::1":
                                self.console.print(ip)
                                return 0
                        # Fallback to localhost
                        self.console.print(next(iter(ips)))
                    return 0
            except ops.pebble.PathError:
                pass

            # Fallback: show localhost
            self.console.print("127.0.0.1")
            return 0
        except Exception as e:
            raise SystemInfoError(f"Failed to get IP address: {e}") from e

    def _show_all_fqdns(self) -> int:
        """Show all FQDNs."""
        try:
            hostname = self._get_hostname()
            fqdns = set([hostname])

            # Look in /etc/hosts for additional names
            try:
                hosts_content = safe_read_file(self.client, "/etc/hosts") or ""

                for line in hosts_content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) >= 2:
                            for name in parts[1:]:
                                if "." in name:  # FQDN
                                    fqdns.add(name)
            except ops.pebble.PathError:
                pass

            for name in sorted(fqdns):
                self.console.print(name)
            return 0
        except Exception as e:
            raise SystemInfoError(f"Failed to get FQDNs: {e}") from e

    def _get_hostname(self) -> str:
        """Get hostname from remote system."""
        # Try /etc/hostname first
        try:
            hostname_content = safe_read_file(self.client, "/etc/hostname")
            hostname = hostname_content.strip() if hostname_content else ""
            if hostname:
                return hostname
        except ops.pebble.PathError:
            pass

        # Try /proc/sys/kernel/hostname
        try:
            hostname = read_proc_file(self.client, "/proc/sys/kernel/hostname").strip()
            if hostname:
                return hostname
        except ops.pebble.PathError:
            pass

        # Fallback to uname nodename
        nodename = self._get_uname_field("nodename")
        if nodename:
            return nodename

        return "localhost"

    def _is_valid_ip(self, ip: str) -> bool:
        """Simple IP address validation."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            return True
        except ValueError:
            return False

    def _get_uname_field(self, field: str) -> str:
        """Get a field from uname via /proc/version or similar."""
        try:
            # Try to read from /proc/sys/kernel/ files
            if field == "nodename":
                try:
                    with self.client.pull(
                        "/proc/sys/kernel/hostname", encoding="utf-8"
                    ) as f:
                        return f.read().strip()
                except ops.pebble.PathError:
                    pass
            elif field == "release":
                try:
                    with self.client.pull(
                        "/proc/sys/kernel/osrelease", encoding="utf-8"
                    ) as f:
                        return f.read().strip()
                except ops.pebble.PathError:
                    pass
            elif field == "version":
                try:
                    with self.client.pull("/proc/version", encoding="utf-8") as f:
                        version_line = f.read().strip()
                        # Extract version info from the version string
                        return version_line
                except ops.pebble.PathError:
                    pass
        except Exception:  # noqa: S110
            # Broad exception handling needed for system info gathering
            pass

        return ""
