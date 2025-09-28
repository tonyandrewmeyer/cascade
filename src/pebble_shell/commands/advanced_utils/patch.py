"""Implementation of PatchCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class PatchCommand(Command):
    """Implementation of patch command."""

    name = "patch"
    help = "Apply patch files to remote files"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Apply patch files to remote files.

Usage: patch [OPTIONS] [ORIGINAL [PATCHFILE]]

Description:
    Apply a patch file to an original file on the remote system.
    Supports unified diff format.

Options:
    -p NUM          Strip NUM leading path components from file names
    -R, --reverse   Apply patch in reverse
    -o FILE         Output to FILE instead of in-place
    -i PATCHFILE    Use PATCHFILE as patch input
    --dry-run       Show what would be done without making changes
    -h, --help      Show this help message

Examples:
    patch -i changes.patch file.txt
    patch -p1 < changes.patch
    patch --dry-run -i test.patch
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the patch command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "p": int,  # strip path components
                "R": bool,  # reverse
                "reverse": bool,
                "o": str,  # output file
                "i": str,  # input patch file
                "dry-run": bool,  # dry run
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        strip_count = flags.get("p", 0)
        reverse = flags.get("R", False) or flags.get("reverse", False)
        output_file = flags.get("o")
        patch_file = flags.get("i")
        dry_run = flags.get("dry-run", False)

        try:
            # Determine patch source and target files
            if patch_file:
                # Patch file specified with -i
                if len(positional_args) == 0:
                    self.console.print("[red]patch: missing target file[/red]")
                    return 1
                target_file = positional_args[0]
            elif len(positional_args) >= 2:
                # patch original patchfile
                target_file = positional_args[0]
                patch_file = positional_args[1]
            elif len(positional_args) == 1:
                # patch original (patch from stdin - not supported)
                self.console.print("[red]patch: reading from stdin not supported[/red]")
                return 1
            else:
                self.console.print("[red]patch: missing arguments[/red]")
                return 1

            # Read patch file
            patch_content = safe_read_file(client, patch_file)
            if patch_content is None:
                self.console.print(
                    f"[red]patch: cannot read patch file '{patch_file}'[/red]"
                )
                return 1

            # Read target file
            original_content = safe_read_file(client, target_file)
            if original_content is None:
                self.console.print(
                    f"[red]patch: cannot read target file '{target_file}'[/red]"
                )
                return 1

            # Apply patch
            try:
                patched_content = self._apply_patch(
                    original_content, patch_content, reverse, strip_count
                )

                if dry_run:
                    self.console.print(
                        f"[green]patch: would patch '{target_file}'[/green]"
                    )
                    return 0

                # Write result
                output_path = output_file if output_file else target_file
                with client.push(output_path, encoding="utf-8") as f:
                    f.write(patched_content)

                self.console.print(
                    f"[green]patch: successfully patched '{output_path}'[/green]"
                )
                return 0

            except Exception as e:
                self.console.print(f"[red]patch: {e}[/red]")
                return 1

        except Exception as e:
            self.console.print(f"[red]patch: {e}[/red]")
            return 1

    def _apply_patch(
        self, original: str, patch_content: str, reverse: bool, strip_count: int
    ) -> str:
        """Apply a unified diff patch to the original content."""
        lines = original.splitlines(keepends=True)
        patch_lines = patch_content.splitlines()

        # Parse patch hunks
        hunks = self._parse_unified_diff(patch_lines, strip_count)

        if reverse:
            # Reverse the patch operations
            hunks = self._reverse_hunks(hunks)

        # Apply hunks in reverse order to maintain line numbers
        for hunk in reversed(hunks):
            lines = self._apply_hunk(lines, hunk)

        return "".join(lines)

    def _parse_unified_diff(
        self, patch_lines: list[str], strip_count: int
    ) -> list[dict]:
        """Parse unified diff format into hunks."""
        hunks = []
        current_hunk = None

        for line in patch_lines:
            if line.startswith("--- ") or line.startswith("+++ "):
                continue  # Skip file headers
            elif line.startswith("@@"):
                # Parse hunk header: @@ -start,count +start,count @@
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if match:
                    old_start, old_count, new_start, new_count = match.groups()
                    current_hunk = {
                        "old_start": int(old_start),
                        "old_count": int(old_count) if old_count else 1,
                        "new_start": int(new_start),
                        "new_count": int(new_count) if new_count else 1,
                        "lines": [],
                    }
                    hunks.append(current_hunk)
            elif current_hunk is not None and (
                line.startswith(" ") or line.startswith("-") or line.startswith("+")
            ):
                current_hunk["lines"].append(line)

        return hunks

    def _reverse_hunks(self, hunks: list[dict]) -> list[dict]:
        """Reverse patch hunks for reverse application."""
        reversed_hunks = []

        for hunk in hunks:
            reversed_hunk = {
                "old_start": hunk["new_start"],
                "old_count": hunk["new_count"],
                "new_start": hunk["old_start"],
                "new_count": hunk["old_count"],
                "lines": [],
            }

            # Reverse the line operations
            for line in hunk["lines"]:
                if line.startswith("+"):
                    reversed_hunk["lines"].append("-" + line[1:])
                elif line.startswith("-"):
                    reversed_hunk["lines"].append("+" + line[1:])
                else:
                    reversed_hunk["lines"].append(line)

            reversed_hunks.append(reversed_hunk)

        return reversed_hunks

    def _apply_hunk(self, lines: list[str], hunk: dict) -> list[str]:
        """Apply a single hunk to the lines."""
        # Convert to 0-based indexing
        start_line = hunk["old_start"] - 1

        # Extract lines to modify
        old_lines = []
        new_lines = []

        for patch_line in hunk["lines"]:
            if patch_line.startswith(" "):
                # Context line
                old_lines.append(patch_line[1:])
                new_lines.append(patch_line[1:])
            elif patch_line.startswith("-"):
                # Removed line
                old_lines.append(patch_line[1:])
            elif patch_line.startswith("+"):
                # Added line
                new_lines.append(patch_line[1:])

        # Replace the section
        end_line = start_line + len(old_lines)
        return lines[:start_line] + new_lines + lines[end_line:]
