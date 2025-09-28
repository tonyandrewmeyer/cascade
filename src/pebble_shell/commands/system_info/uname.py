"""Implementation of UnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UnameCommand(Command):
    """Implementation of uname command."""

    name = "uname"
    help = "Display system information"
    category = "System Information"

    def show_help(self):
        """Show command help."""
        help_text = """Display system information.

Usage: uname [OPTIONS]

Options:
    -h, --help      Show this help message
    -a, --all       Display all information
    -s, --kernel    Display kernel name (default)
    -n, --nodename  Display network node hostname
    -r, --release   Display kernel release
    -v, --version   Display kernel version
    -m, --machine   Display machine hardware name
    -p, --processor Display processor type
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the uname command."""
        self.client = client
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "a": bool,  # all information
                "s": bool,  # kernel name
                "n": bool,  # node name
                "r": bool,  # kernel release
                "v": bool,  # kernel version
                "m": bool,  # machine hardware
                "p": bool,  # processor type
                "i": bool,  # hardware platform
                "o": bool,  # operating system
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        all_info = flags.get("a", False)
        kernel_name = flags.get("s", False)
        node_name = flags.get("n", False)
        kernel_release = flags.get("r", False)
        kernel_version = flags.get("v", False)
        machine = flags.get("m", False)
        processor = flags.get("p", False)
        hardware_platform = flags.get("i", False)
        operating_system = flags.get("o", False)

        try:
            info_parts = []

            if all_info or (
                not any(
                    [
                        kernel_name,
                        node_name,
                        kernel_release,
                        kernel_version,
                        machine,
                        processor,
                        hardware_platform,
                        operating_system,
                    ]
                )
            ):
                # Default behavior or -a flag
                if all_info:
                    info_parts = [
                        self._get_kernel_name(),  # kernel name
                        self._get_node_name(),  # node name
                        self._get_kernel_release(),  # kernel release
                        self._get_kernel_version(),  # kernel version
                        self._get_machine(),  # machine
                        self._get_processor(),  # processor
                        self._get_machine(),  # hardware platform (same as machine)
                        self._get_kernel_name(),  # operating system
                    ]
                else:
                    # Default: just kernel name
                    info_parts = [self._get_kernel_name()]
            else:
                # Specific flags
                if kernel_name:
                    info_parts.append(self._get_kernel_name())
                if node_name:
                    info_parts.append(self._get_node_name())
                if kernel_release:
                    info_parts.append(self._get_kernel_release())
                if kernel_version:
                    info_parts.append(self._get_kernel_version())
                if machine:
                    info_parts.append(self._get_machine())
                if processor:
                    info_parts.append(self._get_processor())
                if hardware_platform:
                    info_parts.append(self._get_machine())
                if operating_system:
                    info_parts.append(self._get_kernel_name())

            self.console.print(" ".join(info_parts))
            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"uname: {e}"))
            return 1

    def _get_help_text(self) -> str:
        """Get help text for the uname command."""
        return """
uname - system information

USAGE:
    uname [OPTIONS]

OPTIONS:
    -a, --all               Print all information
    -s, --kernel-name       Print kernel name (default)
    -n, --nodename          Print network node hostname
    -r, --kernel-release    Print kernel release
    -v, --kernel-version    Print kernel version
    -m, --machine           Print machine hardware name
    -p, --processor         Print processor type
    -i, --hardware-platform Print hardware platform
    -o, --operating-system  Print operating system
    -h, --help              Show this help message

EXAMPLES:
    uname           # Show kernel name
    uname -a        # Show all information
    uname -sr       # Show kernel name and release
"""

    def _get_kernel_name(self) -> str:
        """Get kernel name from remote system."""
        try:
            # Try reading from /proc/version
            version_line = read_proc_file(self.client, "/proc/version").strip()

            # Extract kernel name from version string
            # Format: "Linux version 5.4.0-42-generic ..."
            if version_line.startswith("Linux"):
                return "Linux"

            # Parse the version line to extract OS name
            parts = version_line.split()
            if parts:
                return parts[0]
        except ops.pebble.PathError:
            pass

        # Fallback
        return "Linux"

    def _get_node_name(self) -> str:
        """Get node name (hostname) from remote system."""
        try:
            with self.client.pull("/proc/sys/kernel/hostname", encoding="utf-8") as f:
                return f.read().strip()
        except ops.pebble.PathError:
            pass

        try:
            with self.client.pull("/etc/hostname", encoding="utf-8") as f:
                return f.read().strip()
        except ops.pebble.PathError:
            pass

        return "localhost"

    def _get_kernel_release(self) -> str:
        """Get kernel release from remote system."""
        try:
            return read_proc_file(self.client, "/proc/sys/kernel/osrelease").strip()
        except ops.pebble.PathError:
            pass

        try:
            # Parse from /proc/version
            version_line = read_proc_file(self.client, "/proc/version").strip()

            # Extract version from "Linux version 5.4.0-42-generic ..."
            parts = version_line.split()
            if len(parts) >= 3 and parts[0] == "Linux" and parts[1] == "version":
                return parts[2]
        except ops.pebble.PathError:
            pass

        return "unknown"

    def _get_kernel_version(self) -> str:
        """Get kernel version from remote system."""
        try:
            version_line = read_proc_file(self.client, "/proc/version").strip()
            return version_line
        except ops.pebble.PathError:
            pass

        return "unknown"

    def _get_machine(self) -> str:
        """Get machine hardware name from remote system."""
        try:
            # Try to read from /proc/cpuinfo for architecture info
            cpuinfo = read_proc_file(self.client, "/proc/cpuinfo")

            # Look for architecture information
            for line in cpuinfo.splitlines():
                line = line.strip().lower()
                if line.startswith("architecture"):
                    arch = line.split(":", 1)[1].strip()
                    if "aarch64" in arch or "arm64" in arch:
                        return "aarch64"
                    elif "arm" in arch:
                        return "armv7l"
                elif line.startswith("cpu architecture"):
                    # ARM specific
                    return "armv7l"
                elif "flags" in line and ("lm" in line or "x86_64" in line):
                    return "x86_64"
        except ops.pebble.PathError:
            pass

        # Try ELF header check by looking at /bin/sh
        try:
            with self.client.pull("/bin/sh", encoding="latin-1") as f:
                header = f.read(20)  # Read ELF header

            if header.startswith(b"\x7fELF") and len(header) > 18:
                # Check architecture
                machine_type = header[18:20]
                machine_map = {
                    b"\x3e\x00": "x86_64",  # EM_X86_64
                    b"\x28\x00": "armv7l",  # EM_ARM
                    b"\xb7\x00": "aarch64",  # EM_AARCH64
                }
                if machine_type in machine_map:
                    return machine_map[machine_type]
        except (ops.pebble.PathError, UnicodeDecodeError):
            pass

        return "unknown"

    def _get_processor(self) -> str:
        """Get processor type from remote system."""
        try:
            cpuinfo = read_proc_file(self.client, "/proc/cpuinfo")

            # Look for processor information
            for line in cpuinfo.splitlines():
                line_lower = line.strip().lower()
                if line_lower.startswith("model name"):
                    processor = line.split(":", 1)[1].strip()
                    return processor
                elif line_lower.startswith("processor"):
                    # Some ARM systems
                    processor = line.split(":", 1)[1].strip()
                    if processor and processor != "0":  # Skip processor number
                        return processor
                elif line_lower.startswith("cpu model"):
                    processor = line.split(":", 1)[1].strip()
                    return processor
        except ops.pebble.PathError:
            pass

        # Fallback based on machine type
        machine = self._get_machine()
        if "x86_64" in machine:
            return "x86_64"
        elif "arm" in machine:
            return "ARM"
        elif "aarch64" in machine:
            return "AArch64"

        return "unknown"
