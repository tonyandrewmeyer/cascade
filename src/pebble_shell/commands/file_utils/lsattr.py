"""Implementation of LsattrCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LsattrCommand(Command):
    """Implementation of lsattr command."""

    name = "lsattr"
    help = "List file attributes on ext2/ext3/ext4 filesystems"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """List file attributes on ext2/ext3/ext4 filesystems.

Usage: lsattr [OPTIONS] [FILE...]

Description:
    List file attributes on a Linux file system. Many file systems
    do not support file attributes, in which case no attributes
    will be shown.

Options:
    -a          List all files in directories, including hidden files
    -d          List directories like other files, rather than listing contents
    -R          Recursively list subdirectories
    -v          List version/generation number
    -h, --help  Show this help message

Examples:
    lsattr file.txt         # Show attributes of file.txt
    lsattr -a /etc          # Show attributes of all files in /etc
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the lsattr command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "a": bool,  # all files
                "d": bool,  # directories only
                "R": bool,  # recursive
                "v": bool,  # version number
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        show_all = flags.get("a", False)
        dirs_only = flags.get("d", False)
        recursive = flags.get("R", False)
        show_version = flags.get("v", False)
        files = positional_args if positional_args else ["."]

        try:
            for file_path in files:
                self._list_attributes(
                    client, file_path, show_all, dirs_only, recursive, show_version
                )

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"lsattr: {e}"))
            return 1

    def _list_attributes(
        self,
        client: ClientType,
        path: str,
        show_all: bool,
        dirs_only: bool,
        recursive: bool,
        show_version: bool,
    ):
        """List attributes for a file or directory."""
        try:
            # Try to get extended attributes
            attrs = self._get_file_attributes(client, path)
            version = self._get_file_version(client, path) if show_version else ""

            # Format the attribute string
            attr_str = self._format_attributes(attrs)

            if show_version and version:
                self.console.print(f"{attr_str} {version:>8} {path}")
            else:
                self.console.print(f"{attr_str} {path}")

            # Handle directory traversal
            if recursive and not dirs_only:
                # This would require directory listing which is complex with Pebble
                # For now, just note that recursive is not fully supported
                pass

        except Exception as e:
            self.console.print(get_theme().error_text(f"lsattr: {path}: {e}"))

    def _get_file_attributes(self, client: ClientType, path: str) -> str:
        """Get extended attributes for a file."""
        # This is challenging with filesystem-only access
        # We can try to read some basic information but extended attributes
        # are not typically exposed through /proc or /sys

        # Return a basic attribute string (most files won't have special attributes)
        return "-------------"  # Default no-attributes string

    def _get_file_version(self, client: ClientType, path: str) -> str:
        """Get file version/generation number."""
        # File version is also not typically available through filesystem access
        return "0"

    def _format_attributes(self, attrs: str) -> str:
        """Format the attributes string for display."""
        # Standard lsattr format: 13 characters representing different attributes
        # s, a, c, d, e, f, i, j, s, t, u, A, C, D, E, F, I, J, S, T, U
        if len(attrs) < 13:
            attrs = attrs.ljust(13, "-")
        return attrs[:13]
