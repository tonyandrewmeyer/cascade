"""Implementation of CutCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils import resolve_path
from ...utils.command_helpers import (
    handle_help_flag,
    parse_flags,
    safe_read_file,
    validate_min_args,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CutCommand(Command):
    """Extract columns from files."""

    name = "cut"
    help = "Extract fields or characters from files"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute cut command."""
        # Handle help flag
        if handle_help_flag(self, args):
            return 0

        # Show usage if no arguments
        if len(args) == 0:
            self.console.print("Usage: cut -f fields [-d delimiter] <file> [file2...]")
            self.console.print("       cut -c characters <file> [file2...]")
            self.console.print("Examples:")
            self.console.print("  cut -f 1,3 file.txt        # Extract fields 1 and 3")
            self.console.print(
                "  cut -f 2-4 file.txt        # Extract fields 2 through 4"
            )
            self.console.print(
                "  cut -d: -f 1 /etc/passwd   # Extract usernames from passwd"
            )
            self.console.print("  cut -c 1-5 file.txt        # Extract characters 1-5")
            return 1

        # Parse flags including those with string arguments
        flags_result = parse_flags(args, {"f": str, "c": str, "d": str}, self.shell)
        if flags_result is None:
            return 1
        flags, file_args = flags_result

        # Extract parsed flag values
        fields = flags["f"]
        chars = flags["c"]
        delimiter = flags["d"]

        # Validate file arguments
        if not validate_min_args(
            self.shell, file_args, 1, "cut [-f|-c] <file> [file2...]"
        ):
            return 1

        files = file_args

        if not fields and not chars:
            self.console.print("Usage: cut -f fields [-d delimiter] <file> [file2...]")
            self.console.print("cut: you must specify -f (fields) or -c (characters)")
            return 1

        # Parse field/character specifications
        field_ranges = None
        if fields:
            field_ranges = self._parse_ranges(fields)
            if field_ranges is None:
                self.console.print(f"cut: invalid field specification: {fields}")
                return 1

        char_ranges = None
        if chars:
            char_ranges = self._parse_ranges(chars)
            if char_ranges is None:
                self.console.print(f"cut: invalid character specification: {chars}")
                return 1

        # Process files
        for file_path in files:
            resolved_path = resolve_path(
                self.shell.current_directory, file_path, self.shell.home_dir
            )

            content = safe_read_file(client, resolved_path, self.shell)
            if content is None:
                continue

            for line in content.splitlines():
                if fields:
                    # Extract fields:
                    field_list = line.split(delimiter) if delimiter else line.split()

                    extracted: list[str] = []
                    for start, end in field_ranges or []:
                        extracted.extend(
                            field_list[i]
                            for i in range(start - 1, min(end, len(field_list)))
                            if i >= 0
                        )

                    if delimiter:
                        self.console.print(delimiter.join(extracted))
                    else:
                        self.console.print(" ".join(extracted))

                elif chars:
                    # Extract characters
                    extracted_chars = ""
                    for start, end in char_ranges or []:
                        end = min(end, len(line))
                        if start - 1 < len(line):
                            extracted_chars += line[start - 1 : end]

                    self.console.print(extracted_chars)

        return 0

    def _parse_ranges(self, spec: str) -> list[tuple[int, int]] | None:
        """Parse range specification like '1,3,5-7'."""
        ranges: list[tuple[int, int]] = []
        try:
            for part in spec.split(","):
                if "-" in part and not part.startswith("-"):
                    start, end = part.split("-", 1)
                    start = int(start)
                    end = int(end) if end else start
                    ranges.append((start, end))
                else:
                    num = int(part)
                    ranges.append((num, num))
            return ranges
        except ValueError:
            return None
