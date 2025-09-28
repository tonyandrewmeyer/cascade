"""Tail command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


from ._base import _LinesCommand


class TailCommand(_LinesCommand):
    """Display last lines of a file, with optional -f (follow) support."""

    name = "tail"
    help = "Display last lines of file. Use -f to follow (like tail -f)"

    def process_lines(self, file_lines: Sequence[str], lines: int):
        """Process and display the last lines of a file."""
        for line in file_lines[-lines:]:
            self.shell.console.print(line)
