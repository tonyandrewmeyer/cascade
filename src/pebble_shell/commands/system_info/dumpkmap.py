"""Implementation of DumpkmapCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import read_proc_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DumpkmapCommand(Command):
    """Implementation of dumpkmap command."""

    name = "dumpkmap"
    help = "Display keyboard mapping information"
    category = "System Information"

    def __init__(self, shell: PebbleShell) -> None:
        super().__init__(shell)

    def show_help(self):
        """Show command help."""
        help_text = """Display keyboard mapping information.

Usage: dumpkmap

Description:
    Display keyboard mapping and layout information.

Examples:
    dumpkmap        # Display keyboard mapping
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dumpkmap command."""
        if handle_help_flag(self, args):
            return 0

        try:
            # Try to read keyboard information from various sources
            keymap_info = []

            # Check X11 keyboard settings
            try:
                with client.pull(
                    "/etc/X11/xorg.conf.d/00-keyboard.conf", encoding="utf-8"
                ) as f:
                    content = f.read()
                    for line in content.splitlines():
                        line = line.strip()
                        if "XkbLayout" in line or "XkbVariant" in line:
                            keymap_info.append(f"X11: {line}")
            except ops.pebble.PathError:
                pass

            # Check systemd locale settings
            try:
                with client.pull("/etc/vconsole.conf", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("KEYMAP="):
                            keymap = line.split("=", 1)[1].strip('"')
                            keymap_info.append(f"Console keymap: {keymap}")
            except ops.pebble.PathError:
                pass

            # Check locale settings
            try:
                with client.pull("/etc/locale.conf", encoding="utf-8") as f:
                    content = f.read()
                    for line in content.splitlines():
                        line = line.strip()
                        if line.startswith("LANG="):
                            lang = line.split("=", 1)[1].strip('"')
                            keymap_info.append(f"System locale: {lang}")
            except ops.pebble.PathError:
                pass

            # Check /proc/sys/kernel for keyboard info
            try:
                version = read_proc_file(client, "/proc/sys/kernel/version").strip()
                keymap_info.append(f"Kernel: {version}")
            except ops.pebble.PathError:
                pass

            # Display results
            if keymap_info:
                self.console.print(
                    get_theme().highlight_text("Keyboard Mapping Information:")
                )
                for info in keymap_info:
                    self.console.print(f"  {info}")
            else:
                self.console.print(
                    get_theme().warning_text("No keyboard mapping information found")
                )
                # Show a basic fallback
                self.console.print("Default mapping: US QWERTY")

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"dumpkmap: {e}"))
            return 1
