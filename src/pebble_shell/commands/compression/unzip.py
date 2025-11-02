"""Implementation of UnzipCommand."""

from __future__ import annotations

import io
import os
import zipfile
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, validate_min_args
from .._base import Command
from .exceptions import CompressionError

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UnzipCommand(Command):
    """Implementation of unzip command."""

    name = "unzip"
    help = "Extract files from ZIP archives"
    category = "Compression"

    def __init__(self, shell: shimmer.PebbleCliClient) -> None:
        super().__init__(shell)
        self.shell = shell
        self.console = self.shell.console

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the unzip command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use the common flag parsing code?
        parse_result = parse_flags(
            args,
            {
                "l": bool,  # list contents
                "f": bool,  # force overwrite
                "v": bool,  # verbose
                "d": str,  # extract to directory
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not validate_min_args(
            self.shell, positional_args, 1, "unzip: missing zip file operand"
        ):
            return 1

        zip_file_path = positional_args[0]
        list_contents = flags.get("l", False)
        force = flags.get("f", False)
        verbose = flags.get("v", False)
        extract_dir = flags.get("d") or "."

        try:
            if list_contents:
                return self._list_zip(client, zip_file_path, verbose)
            else:
                return self._extract_zip(
                    client, zip_file_path, extract_dir, force, verbose
                )

        except CompressionError as e:
            self.console.print(f"[red]unzip: {e}[/red]")
            return 1

    def _get_help_text(self) -> str:
        """Get help text for the unzip command."""
        return """
unzip - extract files from ZIP archives

USAGE:
    unzip [OPTIONS] ZIPFILE

OPTIONS:
    -l          List archive contents (don't extract)
    -f          Force overwrite of existing files
    -v          Verbose mode
    -d DIR      Extract files into DIR
    -h, --help  Show this help message

EXAMPLES:
    unzip archive.zip           # Extract all files
    unzip -l archive.zip        # List contents
    unzip -d /tmp archive.zip   # Extract to /tmp
    unzip -v archive.zip        # Extract verbosely
"""

    def _list_zip(
        self,
        client: ClientType,
        zip_file_path: str,
        verbose: bool,
    ) -> int:
        """List contents of a ZIP file."""
        try:
            # Read ZIP file
            with client.pull(zip_file_path, encoding=None) as f:
                zip_content = f.read()

            # Open ZIP file
            zip_buffer = io.BytesIO(zip_content)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                if verbose:
                    self.console.print("Archive:  " + zip_file_path)
                    self.console.print("  Length      Date    Time    Name")
                    self.console.print("---------  ---------- -----   ----")

                    total_size = 0
                    for info in zip_file.infolist():
                        if not info.filename.endswith("/"):  # Skip directories
                            date_time = f"{info.date_time[0]:04d}-{info.date_time[1]:02d}-{info.date_time[2]:02d} {info.date_time[3]:02d}:{info.date_time[4]:02d}"
                            self.console.print(
                                f"{info.file_size:9d}  {date_time}   {info.filename}"
                            )
                            total_size += info.file_size

                    self.console.print("---------                     -------")
                    self.console.print(
                        f"{total_size:9d}                     {len([f for f in zip_file.namelist() if not f.endswith('/')])} files"
                    )
                else:
                    for filename in zip_file.namelist():
                        if not filename.endswith("/"):  # Skip directories
                            self.console.print(filename)

            return 0

        except Exception as e:
            raise CompressionError(f"Failed to list ZIP file: {e}") from e

    def _extract_zip(
        self,
        client: ClientType,
        zip_file_path: str,
        extract_dir: str,
        force: bool,
        verbose: bool,
    ) -> int:
        """Extract files from a ZIP archive."""
        try:
            # Read ZIP file
            with client.pull(zip_file_path, encoding=None) as f:
                zip_content = f.read()

            # Open ZIP file
            zip_buffer = io.BytesIO(zip_content)
            with zipfile.ZipFile(zip_buffer, "r") as zip_file:
                files_to_extract = [
                    info
                    for info in zip_file.infolist()
                    if not info.filename.endswith("/")
                ]
                total_files = len(files_to_extract)
                extracted_count = 0

                for info in files_to_extract:
                    output_path = (
                        os.path.join(extract_dir, info.filename)
                        if extract_dir != "."
                        else info.filename
                    )

                    # Check if file already exists
                    try:
                        client.list_files(output_path)[0]
                        if not force:
                            self.console.print(
                                f"[yellow]Warning: File {info.filename} already exists, skipping (use -f to overwrite)[/yellow]"
                            )
                            continue
                    except (ops.pebble.PathError, IndexError):
                        pass  # File doesn't exist, which is good

                    # Extract file
                    file_content = zip_file.read(info)
                    client.push(output_path, io.BytesIO(file_content), make_dirs=True)

                    if verbose:
                        self.console.print(
                            f"[green]Extracted: {info.filename} ({len(file_content)} bytes)[/green]"
                        )

                    extracted_count += 1

                self.console.print(
                    f"[green]Successfully extracted {extracted_count}/{total_files} files[/green]"
                )
                return 0

        except Exception as e:
            raise CompressionError(f"Failed to extract ZIP file: {e}") from e
