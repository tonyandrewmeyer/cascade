"""Implementation of BzipCommand."""

from __future__ import annotations

import bz2
import io
import os
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, validate_min_args
from .._base import Command
from .exceptions import CompressionError

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class BzipCommand(Command):
    """Implementation of bzip2 command."""

    name = "bzip2"
    help = "Compress or decompress files using bzip2 algorithm"
    category = "Compression"

    def __init__(self, shell: shimmer.PebbleCliClient) -> None:
        super().__init__(shell)
        self.shell = shell
        self.console = self.shell.console

    def execute(
        self,
        client: ClientType,
        args: list[str],
    ) -> int:
        """Execute the bzip2 command."""
        if handle_help_flag(self, args):
            return 0

        # Parse flags
        parse_result = parse_flags(
            args,
            {
                "d": bool,  # decompress
                "f": bool,  # force overwrite
                "k": bool,  # keep original files
                "v": bool,  # verbose
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not validate_min_args(
            self.shell, positional_args, 1, "bzip2: missing file operand"
        ):
            return 1

        decompress = flags.get("d", False)
        force = flags.get("f", False)
        keep_original = flags.get("k", False)
        verbose = flags.get("v", False)

        # Process each file
        for file_path in positional_args:
            # Convert relative paths to absolute paths
            cwd = self.shell.current_directory
            if not os.path.isabs(file_path):
                file_path = os.path.normpath(os.path.join(cwd, file_path))

            try:
                if decompress:
                    success = self._decompress_bzip2(
                        client, file_path, keep_original, force, verbose
                    )
                else:
                    success = self._compress_bzip2(
                        client, file_path, keep_original, force, verbose
                    )

                if not success:
                    return 1
            except CompressionError as e:  # noqa: PERF203
                self.console.print(f"[red]bzip2: {e}[/red]")
                return 1

        return 0

    def _get_help_text(self) -> str:
        """Get help text for the bzip2 command."""
        return """
bzip2 - compress or decompress files using bzip2 algorithm

USAGE:
    bzip2 [OPTIONS] FILE...

OPTIONS:
    -d          Decompress files
    -f          Force overwrite of output files
    -k          Keep (don't delete) input files
    -v          Verbose mode
    -h, --help  Show this help message

EXAMPLES:
    bzip2 file.txt          # Compress file.txt to file.txt.bz2
    bzip2 -d file.txt.bz2   # Decompress file.txt.bz2 to file.txt
    bzip2 -k file.txt       # Compress but keep original file
    bzip2 -v *.txt          # Compress all .txt files verbosely
"""

    def _compress_bzip2(
        self,
        client: ClientType,
        file_path: str,
        keep_original: bool,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Compress a file using bzip2."""
        try:
            # Check if the file is already compressed
            if file_path.endswith(".bz2") and not force:
                self.console.print(
                    f"[yellow]Skipping {file_path} - already appears to be "
                    f"compressed[/yellow]"
                )
                return True

            output_path = file_path + ".bz2"

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

            compressed_content = bz2.compress(file_content)

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

            # Remove original file if not keeping it
            if not keep_original:
                client.remove_path(file_path)

            return True

        except CompressionError:
            raise

    def _decompress_bzip2(
        self,
        client: ClientType,
        file_path: str,
        keep_original: bool,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Decompress a bzip2 file."""
        try:
            # Check if file has .bz2 extension
            if not file_path.endswith(".bz2"):
                raise CompressionError(
                    f"File {file_path} doesn't appear to be a bzip2 file"
                )

            output_path = file_path[:-4]  # Remove .bz2 extension

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
                decompressed_content = bz2.decompress(compressed_content)
            except OSError as e:
                raise CompressionError(
                    f"Failed to decompress - not a valid bzip2 file: {e}"
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

            # Remove original file if not keeping it
            if not keep_original:
                client.remove_path(file_path)

            return True

        except CompressionError:
            raise
