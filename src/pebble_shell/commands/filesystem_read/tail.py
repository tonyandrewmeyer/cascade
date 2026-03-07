"""Tail command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


from ._base import _LinesCommand


class TailCommand(_LinesCommand):
    """Display last lines of a file.

    Usage: tail [-n COUNT] [-c COUNT] [-q] [-v] [file ...]

    Options:
        -n COUNT, --lines=COUNT   Print the last COUNT lines (default 10).
                                  If COUNT starts with ``+``, output begins
                                  at line COUNT (1-indexed, from the start).
        -c COUNT, --bytes=COUNT   Print the last COUNT bytes
        -N                        Legacy shorthand for -n N (e.g. -5)
        -q, --quiet, --silent     Never print filename headers
        -v, --verbose             Always print filename headers

    When multiple files are given, each is preceded by a header
    of the form ``==> filename <==``.
    """

    name = "tail"
    help = "Display last lines of file"

    def process_lines(self, file_lines: Sequence[str], lines: int) -> None:
        """Display last N lines, or from line N if lines is positive offset.

        When the caller passes a positive value produced from ``-n +N``,
        the ``_parse_count`` helper preserves the raw integer.  A value
        >= 1 combined with the ``+`` prefix convention means "starting
        from line N".  We detect this by checking whether the original
        ``lines`` argument came from a ``+`` prefixed string — the base
        class stores that information on ``self._offset_mode``.
        """
        if getattr(self, "_offset_mode", False) and lines >= 1:
            # -n +N: output starting from line N (1-indexed)
            for line in file_lines[lines - 1 :]:
                self.shell.console.print(line)
        else:
            for line in file_lines[-lines:]:
                self.shell.console.print(line)

    def process_bytes(self, content: str, byte_count: int) -> None:
        """Display last N bytes of a file."""
        output = content[-byte_count:]
        if output:
            self.shell.console.print(output, end="")
