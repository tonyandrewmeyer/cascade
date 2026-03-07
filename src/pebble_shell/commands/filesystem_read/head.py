"""Head command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


from ._base import _LinesCommand


class HeadCommand(_LinesCommand):
    """Display first lines of a file.

    Usage: head [-n COUNT] [-c COUNT] [-q] [-v] [file ...]

    Options:
        -n COUNT, --lines=COUNT   Print the first COUNT lines (default 10)
        -c COUNT, --bytes=COUNT   Print the first COUNT bytes
        -N                        Legacy shorthand for -n N (e.g. -5)
        -q, --quiet, --silent     Never print filename headers
        -v, --verbose             Always print filename headers

    When multiple files are given, each is preceded by a header
    of the form ``==> filename <==``.
    """

    name = "head"
    help = "Display first lines of file"

    def process_lines(self, file_lines: Sequence[str], lines: int) -> None:
        """Display first N lines of a file."""
        for line in file_lines[:lines]:
            self.shell.console.print(line)

    def process_bytes(self, content: bytes, byte_count: int) -> None:
        """Display first N bytes of a file."""
        if byte_count == 0:
            return
        output = content[:byte_count]
        if output:
            # Decode for display, replacing incomplete multi-byte sequences
            self.shell.console.print(
                output.decode("utf-8", errors="replace"), end=""
            )
