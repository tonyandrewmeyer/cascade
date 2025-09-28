"""Implementation of CompressCommand."""

from __future__ import annotations

import gzip
import io
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, validate_min_args
from .._base import Command
from .exceptions import CompressionError

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CompressCommand(Command):
    """Implementation of compress command (LZW compression fallback to gzip)."""

    name = "compress"
    help = "Compress files (using gzip as fallback)"
    category = "Compression"

    def __init__(self, shell: shimmer.PebbleCliClient) -> None:
        super().__init__(shell)
        self.shell = shell
        self.console = self.shell.console

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the compress command.

        Note: Since Python doesn't have built-in LZW compression,
        we'll use gzip as a fallback with .Z extension.
        """
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "d": bool,  # decompress
                "f": bool,  # force overwrite
                "v": bool,  # verbose
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        decompress = flags.get("d", False)
        force = flags.get("f", False)
        verbose = flags.get("v", False)

        if not validate_min_args(
            self.shell, positional_args, 1, "compress: missing file operand"
        ):
            return 1

        # Show note about using gzip fallback
        if verbose:
            self.console.print(
                "[yellow]Note: Using gzip compression with .Z extension (LZW not available)[/yellow]"
            )

        # Process each file
        for file_path in positional_args:
            try:
                if decompress:
                    success = self._decompress_file(client, file_path, force, verbose)
                else:
                    success = self._compress_file(client, file_path, force, verbose)

                if not success:
                    return 1
            except CompressionError as e:  # noqa: PERF203
                self.console.print(f"[red]compress: {e}[/red]")
                return 1

        return 0

    def _get_help_text(self) -> str:
        """Get help text for the compress command."""
        return """
compress - compress files (using gzip as fallback)

USAGE:
    compress [OPTIONS] FILE...

OPTIONS:
    -d          Decompress files
    -f          Force overwrite of output files
    -v          Verbose mode
    -h, --help  Show this help message

NOTE:
    This implementation uses gzip compression as a fallback
    since Python doesn't include LZW compression support.
    Files are compressed with .Z extension for compatibility.

EXAMPLES:
    compress file.txt       # Compress file.txt to file.txt.Z
    compress -d file.txt.Z  # Decompress file.txt.Z
"""

    def _compress_file(
        self,
        client: ClientType,
        file_path: str,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Compress a file using gzip (with .Z extension)."""
        try:
            # Check if the file is already compressed
            if file_path.endswith(".Z") and not force:
                self.console.print(
                    f"[yellow]Skipping {file_path} - already appears to be compressed[/yellow]"
                )
                return True

            output_path = file_path + ".Z"

            # Check if output file exists
            try:
                client.list_files(output_path)[0]
                if not force:
                    raise CompressionError(
                        f"Output file {output_path} already exists (use -f to force)"
                    )
            except (ops.pebble.PathError, IndexError):
                pass  # File doesn't exist, which is good

            # Read the input file
            try:
                with client.pull(file_path, encoding=None) as f:
                    file_content = f.read()
            except ops.pebble.PathError as e:
                raise CompressionError(f"Cannot read file: {file_path}") from e

            compressed_content = gzip.compress(file_content)

            # Write compressed content
            client.push(output_path, io.BytesIO(compressed_content), make_dirs=True)

            if verbose:
                original_size = len(file_content)
                compressed_size = len(compressed_content)
                ratio = (
                    (1 - compressed_size / original_size) * 100
                    if original_size > 0
                    else 0
                )
                self.console.print(
                    f"[green]{file_path}: {original_size} -> {compressed_size} bytes ({ratio:.1f}% reduction)[/green]"
                )

            # Remove original file (compress default behavior)
            client.remove_path(file_path)

            return True

        except CompressionError:
            raise

    def _decompress_file(
        self,
        client: ClientType,
        file_path: str,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Decompress a file compressed with compress."""
        try:
            # Check if file has .Z extension
            if not file_path.endswith(".Z"):
                raise CompressionError(
                    f"File {file_path} doesn't appear to be a compress file"
                )

            output_path = file_path[:-2]  # Remove .Z extension

            # Check if output file exists
            try:
                client.list_files(output_path)[0]
                if not force:
                    raise CompressionError(
                        f"Output file {output_path} already exists (use -f to force)"
                    )
            except (ops.pebble.PathError, IndexError):
                pass  # File doesn't exist, which is good

            # Read the compressed file
            try:
                with client.pull(file_path, encoding=None) as f:
                    compressed_content = f.read()
            except ops.pebble.PathError as e:
                raise CompressionError(f"Cannot read file: {file_path}") from e

            try:
                decompressed_content = gzip.decompress(compressed_content)
            except (OSError, gzip.BadGzipFile) as e:
                raise CompressionError(
                    f"Failed to decompress - not a valid compress file: {e}"
                ) from e

            # Write decompressed content
            client.push(output_path, io.BytesIO(decompressed_content), make_dirs=True)

            if verbose:
                compressed_size = len(compressed_content)
                decompressed_size = len(decompressed_content)
                ratio = (
                    (decompressed_size / compressed_size - 1) * 100
                    if compressed_size > 0
                    else 0
                )
                self.console.print(
                    f"[green]{file_path}: {compressed_size} -> {decompressed_size} bytes ({ratio:.1f}% expansion)[/green]"
                )

            # Remove original file (compress default behavior)
            client.remove_path(file_path)

            return True

        except CompressionError:
            raise
