"""Implementation of LzmaCommand."""

from __future__ import annotations

import io
import lzma
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, validate_min_args
from .._base import Command
from .exceptions import CompressionError

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class LzmaCommand(Command):
    """Implementation of lzma command."""

    name = "lzma"
    help = "Compress or decompress files using LZMA algorithm"
    category = "Compression"

    def __init__(self, shell: shimmer.PebbleCliClient) -> None:
        super().__init__(shell)
        self.shell = shell
        self.console = self.shell.console

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the lzma command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use the common flag parsing code?
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
            self.shell, positional_args, 1, "lzma: missing file operand"
        ):
            return 1

        decompress = flags.get("d", False)
        force = flags.get("f", False)
        keep_original = flags.get("k", False)
        verbose = flags.get("v", False)

        # Process each file
        for file_path in positional_args:
            try:
                if decompress:
                    success = self._decompress_lzma(
                        client, file_path, keep_original, force, verbose
                    )
                else:
                    success = self._compress_lzma(
                        client, file_path, keep_original, force, verbose
                    )

                if not success:
                    return 1
            except CompressionError as e:  # noqa: PERF203
                self.console.print(f"[red]lzma: {e}[/red]")
                return 1

        return 0

    def _get_help_text(self) -> str:
        """Get help text for the lzma command."""
        return """
lzma - compress or decompress files using LZMA algorithm

USAGE:
    lzma [OPTIONS] FILE...

OPTIONS:
    -d          Decompress files
    -f          Force overwrite of output files
    -k          Keep (don't delete) input files
    -v          Verbose mode
    -h, --help  Show this help message

EXAMPLES:
    lzma file.txt           # Compress file.txt to file.txt.xz
    lzma -d file.txt.xz     # Decompress file.txt.xz to file.txt
    lzma -k file.txt        # Compress but keep original file
    lzma -v *.txt           # Compress all .txt files verbosely
"""

    def _compress_lzma(
        self,
        client: ClientType,
        file_path: str,
        keep_original: bool,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Compress a file using LZMA."""
        try:
            # Check if the file is already compressed
            if file_path.endswith((".lzma", ".xz")) and not force:
                self.console.print(
                    f"[yellow]Skipping {file_path} - already appears to be compressed[/yellow]"
                )
                return True

            output_path = file_path + ".xz"

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

            compressed_content = lzma.compress(file_content)

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

    def _decompress_lzma(
        self,
        client: ClientType,
        file_path: str,
        keep_original: bool,
        force: bool,
        verbose: bool,
    ) -> bool:
        """Decompress an LZMA file."""
        try:
            # Check if file has .lzma or .xz extension
            if not file_path.endswith((".lzma", ".xz")):
                raise CompressionError(
                    f"File {file_path} doesn't appear to be an LZMA file"
                )

            # Remove extension
            if file_path.endswith(".lzma"):
                output_path = file_path[:-5]
            else:  # .xz
                output_path = file_path[:-3]

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
                decompressed_content = lzma.decompress(compressed_content)
            except (OSError, lzma.LZMAError) as e:
                raise CompressionError(
                    f"Failed to decompress - not a valid LZMA file: {e}"
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
