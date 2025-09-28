"""Unix2dos command for Cascade.

This module provides implementation for the unix2dos command that converts
Unix line endings to DOS format.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file, validate_min_args
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class Unix2dosCommand(Command):
    """Implementation of unix2dos command."""

    name = "unix2dos"
    help = "Convert Unix line endings to DOS"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the unix2dos command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "unix2dos: missing file operand"):
            return 1

        try:
            for file_path in args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                # Convert LF to CRLF (but avoid double conversion)
                dos_content = content.replace("\r\n", "\n").replace("\n", "\r\n")

                # Write back the converted content
                try:
                    client.push(file_path, io.StringIO(dos_content), make_dirs=True)
                    self.console.print(
                        get_theme().success_text(f"unix2dos: converted {file_path}")
                    )
                except ops.pebble.PathError as e:
                    self.console.print(
                        get_theme().error_text(f"unix2dos: {file_path}: {e}")
                    )
                    return 1

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"unix2dos: {e}"))
            return 1
