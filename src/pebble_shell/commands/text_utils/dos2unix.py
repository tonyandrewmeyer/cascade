"""Dos2unix command for Cascade.

This module provides implementation for the dos2unix command that converts
DOS line endings to Unix format.
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


class Dos2unixCommand(Command):
    """Implementation of dos2unix command."""

    name = "dos2unix"
    help = "Convert DOS line endings to Unix"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dos2unix command."""
        if handle_help_flag(self, args):
            return 0

        if not validate_min_args(self.shell, args, 1, "dos2unix: missing file operand"):
            return 1

        try:
            for file_path in args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                # Convert CRLF to LF
                unix_content = content.replace("\r\n", "\n")

                # Write back the converted content
                try:
                    client.push(file_path, io.StringIO(unix_content), make_dirs=True)
                    self.console.print(
                        get_theme().success_text(f"dos2unix: converted {file_path}")
                    )
                except ops.pebble.PathError as e:
                    self.console.print(
                        get_theme().error_text(f"dos2unix: {file_path}: {e}")
                    )
                    return 1

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"dos2unix: {e}"))
            return 1
