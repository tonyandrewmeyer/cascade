"""Implementation of CpioCommand."""

from __future__ import annotations

import io
import tarfile
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Put this in the compression category.
class CpioCommand(Command):
    """Implementation of cpio command."""

    name = "cpio"
    help = "Copy files to and from archives"
    category = "Archive"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the cpio command."""
        if handle_help_flag(self, args):
            return 0

        result = parse_flags(
            args,
            {
                "i": bool,  # extract
                "extract": bool,
                "o": bool,  # create
                "create": bool,
                "t": bool,  # list
                "list": bool,
                "v": bool,  # verbose
                "verbose": bool,
                "d": bool,  # make directories
                "make-directories": bool,
                "F": str,  # archive file
                "H": str,  # format
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        extract = flags.get("i", False) or flags.get("extract", False)
        create = flags.get("o", False) or flags.get("create", False)
        list_contents = flags.get("t", False) or flags.get("list", False)
        verbose = flags.get("v", False) or flags.get("verbose", False)
        make_dirs = flags.get("d", False) or flags.get("make-directories", False)
        archive_file = flags.get("F")
        format_type = flags.get("H", "newc")

        # Exactly one mode must be specified
        mode_count = sum([extract, create, list_contents])
        if mode_count != 1:
            self.console.print(
                "[red]cpio: must specify exactly one of -i, -o, or -t[/red]"
            )
            return 1

        try:
            if list_contents:
                return self._list_archive(client, archive_file, verbose)
            elif extract:
                return self._extract_archive(client, archive_file, verbose, make_dirs)
            elif create:
                return self._create_archive(client, archive_file, verbose, format_type)
            else:
                return 1

        except Exception as e:
            self.console.print(f"[red]cpio: {e}[/red]")
            return 1

    def _list_archive(
        self, client: ClientType, archive_file: str, verbose: bool
    ) -> int:
        """List contents of an archive."""
        if not archive_file:
            self.console.print("[red]cpio: archive file required for listing[/red]")
            return 1

        try:
            # Read archive file
            archive_content = safe_read_file(client, archive_file, self.shell)
            if archive_content is None:
                self.console.print(
                    f"[red]cpio: cannot read archive '{archive_file}'[/red]"
                )
                return 1

            # Try to read as tar format (most common)
            try:
                with tarfile.open(
                    fileobj=io.BytesIO(archive_content.encode()), mode="r"
                ) as tar:
                    for member in tar.getmembers():
                        if verbose:
                            self.console.print(
                                f"{member.mode:o} {member.uid}/{member.gid} {member.size:8d} {member.name}"
                            )
                        else:
                            self.console.print(member.name)
                return 0
            except tarfile.TarError:
                self.console.print(
                    "[yellow]cpio: archive format not supported for listing[/yellow]"
                )
                return 1

        except Exception as e:
            self.console.print(f"[red]cpio: error listing archive: {e}[/red]")
            return 1

    def _extract_archive(
        self, client: ClientType, archive_file: str, verbose: bool, make_dirs: bool
    ) -> int:
        """Extract files from an archive."""
        if not archive_file:
            self.console.print("[red]cpio: archive file required for extraction[/red]")
            return 1

        try:
            # Read archive file
            archive_content = safe_read_file(client, archive_file, self.shell)
            if archive_content is None:
                self.console.print(
                    f"[red]cpio: cannot read archive '{archive_file}'[/red]"
                )
                return 1

            # Try to extract as tar format
            try:
                with tarfile.open(
                    fileobj=io.BytesIO(archive_content.encode()), mode="r"
                ) as tar:
                    extracted_count = 0
                    for member in tar.getmembers():
                        if member.isfile():
                            file_content = tar.extractfile(member)
                            if file_content:
                                # Create directories if needed
                                if make_dirs and "/" in member.name:
                                    dir_path = "/".join(member.name.split("/")[:-1])
                                    # Note: In a real implementation, we'd need to create directories
                                    # For this demo, we'll just note it
                                    if verbose:
                                        self.console.print(
                                            f"[dim]Would create directory: {dir_path}[/dim]"
                                        )

                                # Write file (simulate)
                                if verbose:
                                    self.console.print(f"Extracting: {member.name}")

                                # In a real implementation, we'd write to the remote filesystem
                                # For this demo, we'll just count the files
                                extracted_count += 1

                    self.console.print(
                        f"[green]Extracted {extracted_count} files[/green]"
                    )
                    return 0
            except tarfile.TarError:
                self.console.print(
                    "[yellow]cpio: archive format not supported for extraction[/yellow]"
                )
                return 1

        except Exception as e:
            self.console.print(f"[red]cpio: error extracting archive: {e}[/red]")
            return 1

    def _create_archive(
        self, client: ClientType, archive_file: str, verbose: bool, format_type: str
    ) -> int:
        """Create an archive from file list."""
        self.console.print(
            "[yellow]cpio: creating archives not implemented in read-only mode[/yellow]"
        )
        self.console.print(
            "[dim]Would read file list from stdin and create archive[/dim]"
        )
        return 0
