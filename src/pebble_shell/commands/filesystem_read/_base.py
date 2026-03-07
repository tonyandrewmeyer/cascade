"""Base classes for filesystem read commands."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    import ops
    import shimmer

from ...utils.command_helpers import (
    handle_help_flag,
    process_file_arguments,
    safe_read_file,
    safe_read_file_lines,
)
from .._base import Command


def _parse_head_tail_args(
    args: list[str],
) -> tuple[int, int | None, bool | None, bool, list[str]]:
    """Parse arguments for head/tail commands with POSIX-compatible flags.

    Supports:
        -n COUNT / --lines=COUNT / --lines COUNT: line count
        -c COUNT / --bytes=COUNT / --bytes COUNT: byte count
        -N (e.g. -5): legacy shorthand for -n N
        -q / --quiet / --silent: suppress headers
        -v / --verbose: always show headers
        bare number (e.g. ``head 10 file``): legacy line count

    For tail, -n +N means "starting from line N" (offset from beginning).

    Returns:
        Tuple of (line_count, byte_count, quiet_flag, offset_mode,
        remaining_args).  ``quiet_flag`` is ``True`` for quiet, ``False``
        for verbose, ``None`` for default behaviour.  ``offset_mode`` is
        ``True`` when the line count was specified with a ``+`` prefix
        (e.g. ``-n +3``).
    """
    lines = 10
    byte_count: int | None = None
    quiet: bool | None = None
    offset_mode = False
    remaining: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]

        # Long flags --lines, --bytes, --quiet, --silent, --verbose
        if arg.startswith("--"):
            flag = arg[2:]
            key, _, value = flag.partition("=")

            if key in ("lines", "bytes"):
                if not value:
                    if i + 1 >= len(args):
                        remaining.append(arg)
                        i += 1
                        continue
                    value = args[i + 1]
                    i += 1
                if key == "lines":
                    if value.startswith("+"):
                        offset_mode = True
                    lines = _parse_count(value)
                else:
                    byte_count = _parse_count(value)
            elif key in ("quiet", "silent"):
                quiet = True
            elif key == "verbose":
                quiet = False
            else:
                remaining.append(arg)
            i += 1
            continue

        # Short flags
        if arg.startswith("-") and len(arg) > 1:
            # Check for legacy -N form (e.g. -5)
            if re.fullmatch(r"-\d+", arg):
                lines = int(arg[1:])
                i += 1
                continue

            flag_char = arg[1]

            if flag_char == "n":
                # -nVALUE or -n VALUE
                rest = arg[2:]
                if rest:
                    if rest.startswith("+"):
                        offset_mode = True
                    lines = _parse_count(rest)
                elif i + 1 < len(args):
                    i += 1
                    value = args[i]
                    if value.startswith("+"):
                        offset_mode = True
                    lines = _parse_count(value)
                i += 1
                continue

            if flag_char == "c":
                rest = arg[2:]
                if rest:
                    byte_count = _parse_count(rest)
                elif i + 1 < len(args):
                    i += 1
                    byte_count = _parse_count(args[i])
                i += 1
                continue

            if flag_char == "q":
                quiet = True
                i += 1
                continue

            if flag_char == "v":
                quiet = False
                i += 1
                continue

            # Unknown flag - pass through as a filename
            remaining.append(arg)
            i += 1
            continue

        # Bare number (legacy form)
        if arg.isdigit():
            lines = int(arg)
            i += 1
            continue

        remaining.append(arg)
        i += 1

    return lines, byte_count, quiet, offset_mode, remaining


def _parse_count(value: str) -> int:
    """Parse a count value, preserving the sign for values like ``+3``."""
    return int(value)


class _LinesCommand(Command):
    """Base class for commands that read lines from a file."""

    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute command."""
        if handle_help_flag(self, args):
            return 0

        lines, byte_count, quiet, offset_mode, remaining_args = _parse_head_tail_args(
            args
        )
        self._offset_mode = offset_mode

        if not remaining_args:
            from ...utils.theme import get_theme

            theme = get_theme()
            self.shell.console.print(
                theme.error_text("Error: At least 1 argument(s) required")
            )
            return 1

        file_paths = process_file_arguments(
            self.shell, client, remaining_args, allow_globs=True, min_files=1
        )
        if file_paths is None:
            return 1

        # Determine whether to show headers
        show_headers: bool
        if quiet is True:
            show_headers = False
        elif quiet is False:
            show_headers = True
        else:
            show_headers = len(file_paths) > 1

        exit_code = 0
        for idx, file_path in enumerate(file_paths):
            # Print filename header
            if show_headers:
                if idx > 0:
                    self.shell.console.print("")
                self.shell.console.print(f"==> {file_path} <==")

            if byte_count is not None:
                # Byte mode
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    exit_code = 1
                    continue
                self.process_bytes(content, byte_count)
            else:
                # Line mode
                file_lines = safe_read_file_lines(client, file_path, self.shell)
                if file_lines is None:
                    exit_code = 1
                    continue
                self.process_lines(file_lines, lines)

        return exit_code

    def process_lines(self, file_lines: Sequence[str], lines: int) -> None:
        """Process lines read from the file."""
        raise NotImplementedError("Subclasses must implement process_lines method")

    def process_bytes(self, content: str, byte_count: int) -> None:
        """Process bytes read from the file."""
        raise NotImplementedError("Subclasses must implement process_bytes method")
