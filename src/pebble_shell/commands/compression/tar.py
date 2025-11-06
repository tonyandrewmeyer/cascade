"""Implementation of TarCommand."""

from __future__ import annotations

import io
import os
import tarfile
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command
from .exceptions import CompressionError

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TarCommand(Command):
    """Implementation of tar command."""

    name = "tar"
    help = "Archive files"
    category = "Compression"

    def __init__(self, shell: shimmer.PebbleCliClient) -> None:
        super().__init__(shell)
        self.shell = shell
        self.console = self.shell.console

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the tar command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use the common flag parsing code?
        parse_result = parse_flags(
            args,
            {
                "c": bool,  # create archive
                "x": bool,  # extract archive
                "t": bool,  # list archive contents
                "f": str,  # archive filename
                "z": bool,  # gzip compression
                "j": bool,  # bzip2 compression
                "J": bool,  # xz compression
                "v": bool,  # verbose
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        create = flags.get("c", False)
        extract = flags.get("x", False)
        list_contents = flags.get("t", False)
        archive_filename = flags.get("f")
        gzip_compress = flags.get("z", False)
        bzip2_compress = flags.get("j", False)
        xz_compress = flags.get("J", False)
        verbose = flags.get("v", False)

        # Validate arguments
        mode_count = sum([create, extract, list_contents])
        if mode_count != 1:
            self.console.print(
                "[red]tar: must specify exactly one of -c, -x, or -t[/red]"
            )
            return 1

        if not archive_filename:
            self.console.print("[red]tar: must specify archive filename with -f[/red]")
            return 1

        # Convert relative paths to absolute paths
        cwd = self.shell.current_directory
        if not os.path.isabs(archive_filename):
            archive_filename = os.path.normpath(os.path.join(cwd, archive_filename))

        # Convert file paths to absolute paths
        positional_args = [
            os.path.normpath(os.path.join(cwd, path)) if not os.path.isabs(path) else path
            for path in positional_args
        ]

        try:
            if create:
                if not positional_args:
                    self.console.print(
                        "[red]tar: no files specified for archive creation[/red]"
                    )
                    return 1

                compression_type = None
                if gzip_compress:
                    compression_type = "gz"
                elif bzip2_compress:
                    compression_type = "bz2"
                elif xz_compress:
                    compression_type = "xz"

                return self._create_tar(
                    client, archive_filename, positional_args, compression_type, verbose
                )

            elif extract:
                return self._extract_tar(
                    client, archive_filename, positional_args, verbose
                )

            elif list_contents:
                return self._list_tar(client, archive_filename, verbose)

        except CompressionError as e:
            self.console.print(f"[red]tar: {e}[/red]")
            return 1

        return 0

    def _get_help_text(self) -> str:
        """Get help text for the tar command."""
        return """
tar - archive files

USAGE:
    tar [OPTIONS] -f ARCHIVE [FILES...]

OPTIONS:
    -c          Create a new archive
    -x          Extract files from archive
    -t          List archive contents
    -f FILE     Use archive file FILE
    -z          Filter archive through gzip
    -j          Filter archive through bzip2
    -J          Filter archive through xz
    -v          Verbose mode
    -h, --help  Show this help message

EXAMPLES:
    tar -czf archive.tar.gz dir/        # Create gzipped tar archive
    tar -xzf archive.tar.gz             # Extract gzipped tar archive
    tar -tzf archive.tar.gz             # List contents of gzipped archive
    tar -cf archive.tar file1 file2     # Create uncompressed archive
"""

    def _create_tar(
        self,
        client: ClientType,
        archive_path: str,
        files: list[str],
        compression: str | None,
        verbose: bool,
    ) -> int:
        """Create a tar archive."""
        try:
            # Determine compression mode
            mode = "w"
            if compression == "gz":
                mode = "w:gz"
            elif compression == "bz2":
                mode = "w:bz2"
            elif compression == "xz":
                mode = "w:xz"

            # Create tar archive in memory
            tar_buffer = io.BytesIO()

            with tarfile.open(fileobj=tar_buffer, mode=mode) as tar:
                for file_path in files:
                    self._add_to_tar(client, tar, file_path, verbose)

            # Write archive to destination
            tar_buffer.seek(0)
            client.push(archive_path, tar_buffer, make_dirs=True)

            if verbose:
                self.console.print(f"[green]Created archive: {archive_path}[/green]")

            return 0

        except Exception as e:
            raise CompressionError(f"Failed to create archive: {e}") from e

    def _add_to_tar(
        self,
        client: ClientType,
        tar: tarfile.TarFile,
        file_path: str,
        verbose: bool,
    ) -> None:
        """Add a file to the tar archive."""
        try:
            # Try to read as file first
            with client.pull(file_path, encoding=None) as f:
                file_content = f.read()

            # Add file to tar
            tarinfo = tarfile.TarInfo(name=file_path)
            tarinfo.size = len(file_content)
            tar.addfile(tarinfo, io.BytesIO(file_content))

            if verbose:
                self.console.print(f"[green]Added: {file_path}[/green]")

        except ops.pebble.PathError:
            # Try as directory - for simplicity, we'll just skip directories in this basic implementation
            if verbose:
                self.console.print(f"[yellow]Skipping directory: {file_path}[/yellow]")

    def _extract_tar(
        self,
        client: ClientType,
        archive_path: str,
        specific_files: list[str],
        verbose: bool,
    ) -> int:
        """Extract files from a tar archive."""
        try:
            # Read archive
            with client.pull(archive_path, encoding=None) as f:
                archive_content = f.read()

            # Open tar archive
            archive_buffer = io.BytesIO(archive_content)
            with tarfile.open(fileobj=archive_buffer, mode="r:*") as tar:
                members = tar.getmembers()

                # Filter members if specific files requested
                if specific_files:
                    members = [m for m in members if m.name in specific_files]

                extracted_count = 0
                for member in members:
                    if member.isfile():
                        # Extract file
                        file_content = tar.extractfile(member)
                        if file_content:
                            content = file_content.read()
                            client.push(
                                member.name, io.BytesIO(content), make_dirs=True
                            )
                            extracted_count += 1

                            if verbose:
                                self.console.print(
                                    f"[green]Extracted: {member.name}[/green]"
                                )

                self.console.print(
                    f"[green]Successfully extracted {extracted_count} files[/green]"
                )
                return 0

        except Exception as e:
            raise CompressionError(f"Failed to extract archive: {e}") from e

    def _list_tar(
        self,
        client: ClientType,
        archive_path: str,
        verbose: bool,
    ) -> int:
        """List contents of a tar archive."""
        try:
            # Read archive
            with client.pull(archive_path, encoding=None) as f:
                archive_content = f.read()

            # Open tar archive
            archive_buffer = io.BytesIO(archive_content)
            with tarfile.open(fileobj=archive_buffer, mode="r:*") as tar:
                members = tar.getmembers()

                for member in members:
                    if verbose:
                        # Show detailed info like ls -l
                        mode_str = self._get_file_mode_string(member)
                        size_str = str(member.size).rjust(8)
                        self.console.print(f"{mode_str} {size_str} {member.name}")
                    else:
                        self.console.print(member.name)

                return 0

        except Exception as e:
            raise CompressionError(f"Failed to list archive: {e}") from e

    def _get_file_mode_string(self, member: tarfile.TarInfo) -> str:
        """Convert file mode to string representation."""
        mode = member.mode or 0o644
        type_char = "-"

        if member.isdir():
            type_char = "d"
        elif member.islnk() or member.issym():
            type_char = "l"

        # Convert mode to string (simplified)
        perms = []
        for i in range(3):
            val = (mode >> (6 - i * 3)) & 7
            perm = ""
            perm += "r" if val & 4 else "-"
            perm += "w" if val & 2 else "-"
            perm += "x" if val & 1 else "-"
            perms.append(perm)

        return type_char + "".join(perms)
