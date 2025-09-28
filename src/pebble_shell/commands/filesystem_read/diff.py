"""Diff command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import shimmer

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, validate_min_args
from .._base import Command


class DiffCommand(Command):
    """Compare files line by line."""

    name = "diff"
    help = "Compare files line by line. Use -r for recursive directory comparison"
    category = "Filesystem Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute diff command."""
        if handle_help_flag(self, args):
            return 0

        flags_result = parse_flags(args, {"r": bool}, self.shell)
        if flags_result is None:
            return 1
        flags, remaining_args = flags_result

        if not validate_min_args(
            self.shell, remaining_args, 2, "diff [-r] file1 file2"
        ):
            return 1

        if len(remaining_args) > 2:
            self.shell.console.print("Error: Too many arguments")
            return 1

        file1, file2 = remaining_args[0], remaining_args[1]
        recursive = flags["r"]

        # Check if files exist
        try:
            stat1 = client.list_files(file1)
            stat2 = client.list_files(file2)
        except Exception as e:
            self.shell.console.print(f"Error accessing files: {e}")
            return 1

        # If both are directories and recursive is enabled
        if recursive and len(stat1) > 0 and len(stat2) > 0:
            return self._compare_directories(client, file1, file2)
        return self._compare_files(client, file1, file2)

    def _compare_files(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        file1: str,
        file2: str,
    ) -> int:
        """Compare two files line by line."""
        try:
            # Read both files
            with client.pull(file1) as f1:
                content1 = f1.read()
                assert isinstance(content1, str)
                lines1 = content1.splitlines()

            with client.pull(file2) as f2:
                content2 = f2.read()
                assert isinstance(content2, str)
                lines2 = content2.splitlines()

            # Simple diff algorithm
            differences: list[tuple[int, str | None, str | None]] = []
            max_len = max(len(lines1), len(lines2))

            for i in range(max_len):
                line1 = lines1[i] if i < len(lines1) else None
                line2 = lines2[i] if i < len(lines2) else None

                if line1 != line2:
                    differences.append((i + 1, line1, line2))

            # Display results
            if not differences:
                self.shell.console.print("Files are identical")
                return 0

            self.shell.console.print(f"--- {file1}")
            self.shell.console.print(f"+++ {file2}")
            self.shell.console.print()

            for line_num, line1, line2 in differences:
                if line1 is None:
                    # Line only in file2
                    self.shell.console.print(f"@@ Line {line_num} @@")
                    self.shell.console.print(f"+{line2}")
                elif line2 is None:
                    # Line only in file1
                    self.shell.console.print(f"@@ Line {line_num} @@")
                    self.shell.console.print(f"-{line1}")
                else:
                    # Different lines
                    self.shell.console.print(f"@@ Line {line_num} @@")
                    self.shell.console.print(f"-{line1}")
                    self.shell.console.print(f"+{line2}")
                self.shell.console.print()

            return 1

        except Exception as e:
            self.shell.console.print(f"Error comparing files: {e}")
            return 1

    def _compare_directories(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, dir1: str, dir2: str
    ) -> int:
        """Compare two directories recursively."""
        try:
            # Get all files in both directories
            files1 = self._get_all_files(client, dir1)
            files2 = self._get_all_files(client, dir2)

            # Find common files
            common_files = set(files1.keys()) & set(files2.keys())
            only_in_1 = set(files1.keys()) - set(files2.keys())
            only_in_2 = set(files2.keys()) - set(files1.keys())

            differences_found = False

            # Show files only in dir1
            if only_in_1:
                self.shell.console.print(f"Files only in {dir1}:")
                for file in sorted(only_in_1):
                    self.shell.console.print(f"  {file}")
                self.shell.console.print()
                differences_found = True

            # Show files only in dir2
            if only_in_2:
                self.shell.console.print(f"Files only in {dir2}:")
                for file in sorted(only_in_2):
                    self.shell.console.print(f"  {file}")
                self.shell.console.print()
                differences_found = True

            # Compare common files
            for file in sorted(common_files):
                file1_path = f"{dir1}/{file}"
                file2_path = f"{dir2}/{file}"

                try:
                    # Quick size check
                    stat1 = client.list_files(file1_path)
                    stat2 = client.list_files(file2_path)

                    if len(stat1) != len(stat2):
                        self.shell.console.print(f"Files differ: {file}")
                        differences_found = True
                        continue

                    # Compare content
                    with client.pull(file1_path) as f1:
                        content1 = f1.read()

                    with client.pull(file2_path) as f2:
                        content2 = f2.read()

                    if content1 != content2:
                        self.shell.console.print(f"Files differ: {file}")
                        differences_found = True

                except Exception:
                    self.shell.console.print(f"Error comparing {file}")
                    differences_found = True

            if not differences_found:
                self.shell.console.print("Directories are identical")
                return 0

            return 1

        except Exception as e:
            self.shell.console.print(f"Error comparing directories: {e}")
            return 1

    def _get_all_files(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, directory: str
    ) -> dict[str, str]:
        """Get all files in a directory recursively."""
        try:
            entries = client.list_files(directory)
        except ops.pebble.PathError as e:
            self.shell.console.print(f"Error listing files in {directory}: {e}")
            return {}

        files: dict[str, str] = {}
        for entry in entries:
            if entry.type == ops.pebble.FileType.FILE:
                # Remove directory prefix for relative path:
                rel_path = entry.path[len(directory) :].lstrip("/")
                files[rel_path] = entry.path
            elif entry.type == ops.pebble.FileType.DIRECTORY:
                # Recursively get files in subdirectory:
                subdir_files = self._get_all_files(client, entry.path)
                for rel_path, full_path in subdir_files.items():
                    files[rel_path] = full_path
        return files
