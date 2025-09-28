"""Split command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class SplitCommand(Command):
    """Implementation of split command."""

    name = "split"
    help = "Split a file into pieces"
    category = "Data Processing"

    def show_help(self):
        """Show command help."""
        help_text = """Split a file into pieces.

Usage: split [OPTIONS] [INPUT [PREFIX]]

Description:
    Output fixed-size pieces of INPUT to PREFIXaa, PREFIXab, ...
    Default PREFIX is 'x'.

Options:
    -a SUFFIX_LENGTH Use SUFFIX_LENGTH characters for suffix (default: 2)
    -b SIZE         Put SIZE bytes per output file
    -C SIZE         Put at most SIZE bytes per line per output file
    -l NUMBER       Put NUMBER lines per output file (default: 1000)
    -d              Use numeric suffixes instead of alphabetic
    --verbose       Print a diagnostic just before each output file is opened
    -h, --help      Show this help message

SIZE can be:
    N               N bytes
    Nk or NK        N kilobytes
    Nm or NM        N megabytes
    Ng or NG        N gigabytes

Examples:
    split file.txt
    split -l 500 file.txt part_
    split -b 1024 file.txt chunk_
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the split command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use common flag parsing code?
        parse_result = parse_flags(
            args,
            {
                "a": str,  # suffix length
                "b": str,  # bytes per file
                "C": str,  # bytes per line per file
                "l": str,  # lines per file
                "d": bool,  # numeric suffixes
                "verbose": bool,  # verbose output
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        suffix_length = int(flags.get("a", 2))
        bytes_per_file = self._parse_size(flags.get("b", None))
        bytes_per_line = self._parse_size(flags.get("C", None))
        lines_per_file = int(flags.get("l", 1000)) if flags.get("l") else 1000
        numeric_suffix = flags.get("d", False)
        verbose = flags.get("verbose", False)

        # Get input file and prefix
        input_file = positional_args[0] if positional_args else "-"
        prefix = positional_args[1] if len(positional_args) > 1 else "x"

        # Determine split mode
        if bytes_per_file:
            split_mode = "bytes"
            split_size = bytes_per_file
        elif bytes_per_line:
            split_mode = "line_bytes"
            split_size = bytes_per_line
        else:
            split_mode = "lines"
            split_size = lines_per_file

        try:
            # Read input
            if input_file == "-":
                # TODO: Handle stdin
                self.console.print(
                    get_theme().warning_text("split: reading from stdin not supported")
                )
                return 1
            else:
                content = safe_read_file(client, input_file, self.shell)
                if content is None:
                    return 1

            # Split the content
            if split_mode == "lines":
                self._split_by_lines(
                    client,
                    content,
                    prefix,
                    split_size,
                    suffix_length,
                    numeric_suffix,
                    verbose,
                )
            elif split_mode == "bytes":
                self._split_by_bytes(
                    client,
                    content,
                    prefix,
                    split_size,
                    suffix_length,
                    numeric_suffix,
                    verbose,
                )
            elif split_mode == "line_bytes":
                self._split_by_line_bytes(
                    client,
                    content,
                    prefix,
                    split_size,
                    suffix_length,
                    numeric_suffix,
                    verbose,
                )

            return 0

        except ops.pebble.PathError:
            self.console.print(
                get_theme().error_text(
                    f"split: {input_file}: No such file or directory"
                )
            )
            return 1
        except Exception as e:
            self.console.print(get_theme().error_text(f"split: {e}"))
            return 1

    def _parse_size(self, size_str: str | None) -> int | None:
        """Parse size string (e.g., '1024', '1K', '1M')."""
        if not size_str:
            return None

        size_str = size_str.upper()
        multipliers = {
            "K": 1024,
            "M": 1024 * 1024,
            "G": 1024 * 1024 * 1024,
        }

        if size_str[-1] in multipliers:
            return int(size_str[:-1]) * multipliers[size_str[-1]]
        else:
            return int(size_str)

    def _generate_suffix(self, index: int, length: int, numeric: bool) -> str:
        """Generate suffix for split files."""
        if numeric:
            return f"{index:0{length}d}"
        else:
            # Alphabetic suffix (aa, ab, ac, ..., ba, bb, ...)
            suffix = ""
            remaining = index
            for _ in range(length):
                suffix = chr(ord("a") + (remaining % 26)) + suffix
                remaining //= 26
            return suffix

    def _split_by_lines(
        self,
        client: ClientType,
        content: str,
        prefix: str,
        lines_per_file: int,
        suffix_length: int,
        numeric_suffix: bool,
        verbose: bool,
    ):
        """Split content by number of lines."""
        lines = content.splitlines(keepends=True)

        for file_index, i in enumerate(range(0, len(lines), lines_per_file)):
            chunk_lines = lines[i : i + lines_per_file]
            chunk_content = "".join(chunk_lines)

            suffix = self._generate_suffix(file_index, suffix_length, numeric_suffix)
            output_filename = f"{prefix}{suffix}"

            if verbose:
                self.console.print(f"creating file '{output_filename}'")

            # Write to remote file
            from io import StringIO

            output_stream = StringIO(chunk_content)
            client.push(output_filename, output_stream)

    def _split_by_bytes(
        self,
        client: ClientType,
        content: str,
        prefix: str,
        bytes_per_file: int,
        suffix_length: int,
        numeric_suffix: bool,
        verbose: bool,
    ):
        """Split content by number of bytes."""
        content_bytes = content.encode("utf-8")

        for file_index, i in enumerate(range(0, len(content_bytes), bytes_per_file)):
            chunk_bytes = content_bytes[i : i + bytes_per_file]

            suffix = self._generate_suffix(file_index, suffix_length, numeric_suffix)
            output_filename = f"{prefix}{suffix}"

            if verbose:
                self.console.print(f"creating file '{output_filename}'")

            # Write to remote file
            from io import BytesIO

            output_stream = BytesIO(chunk_bytes)
            client.push(output_filename, output_stream)

    def _split_by_line_bytes(
        self,
        client: ClientType,
        content: str,
        prefix: str,
        bytes_per_line: int,
        suffix_length: int,
        numeric_suffix: bool,
        verbose: bool,
    ):
        """Split content by bytes per line."""
        lines = content.splitlines(keepends=True)
        file_index = 0
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line.encode("utf-8"))

            if current_size + line_size > bytes_per_line and current_chunk:
                # Save current chunk
                chunk_content = "".join(current_chunk)
                suffix = self._generate_suffix(
                    file_index, suffix_length, numeric_suffix
                )
                output_filename = f"{prefix}{suffix}"

                if verbose:
                    self.console.print(f"creating file '{output_filename}'")

                from io import StringIO

                output_stream = StringIO(chunk_content)
                client.push(output_filename, output_stream)

                file_index += 1
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        # Save final chunk if any
        if current_chunk:
            chunk_content = "".join(current_chunk)
            suffix = self._generate_suffix(file_index, suffix_length, numeric_suffix)
            output_filename = f"{prefix}{suffix}"

            if verbose:
                self.console.print(f"creating file '{output_filename}'")

            from io import StringIO

            output_stream = StringIO(chunk_content)
            client.push(output_filename, output_stream)
