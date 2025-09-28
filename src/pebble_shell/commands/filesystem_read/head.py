"""Head command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


from ._base import _LinesCommand


class HeadCommand(_LinesCommand):
    """Display first lines of a file."""

    name = "head"
    help = "Display first lines of file"

    def process_lines(self, file_lines: Sequence[str], lines: int):
        """Display first lines of a file."""
        for line in file_lines[:lines]:
            self.shell.console.print(line)
