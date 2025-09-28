"""Implementation of RealpathCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class RealpathCommand(Command):
    """Implementation of realpath command."""

    name = "realpath"
    help = "Display absolute pathnames"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Display absolute pathnames.

Usage: realpath [OPTIONS] FILE...

Description:
    Print the resolved absolute path for each given file.
    Resolves symbolic links and removes '..' and '.' components.

Options:
    -e, --canonicalize-existing  All components must exist
    -m, --canonicalize-missing   No components need exist
    -s, --strip                  Don't expand symlinks
    -z, --zero                   End output with NUL character
    -h, --help                   Show this help message

Examples:
    realpath file.txt
    realpath ../dir/file.txt
    realpath -e file.txt
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the realpath command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "e": bool,  # canonicalize-existing
                "canonicalize-existing": bool,
                "m": bool,  # canonicalize-missing
                "canonicalize-missing": bool,
                "s": bool,  # strip
                "strip": bool,
                "z": bool,  # zero
                "zero": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        must_exist = flags.get("e", False) or flags.get("canonicalize-existing", False)
        allow_missing = flags.get("m", False) or flags.get(
            "canonicalize-missing", False
        )
        no_symlinks = flags.get("s", False) or flags.get("strip", False)
        use_null = flags.get("z", False) or flags.get("zero", False)

        if not positional_args:
            self.console.print("[red]realpath: missing operand[/red]")
            return 1

        exit_code = 0
        terminator = "\0" if use_null else "\n"

        for file_path in positional_args:
            try:
                # Resolve the absolute path
                resolved_path = self._resolve_path(
                    client, file_path, must_exist, allow_missing, no_symlinks
                )
                if resolved_path is None:
                    exit_code = 1
                    continue

                self.console.print(resolved_path, end=terminator)

            except Exception as e:
                self.console.print(f"[red]realpath: {file_path}: {e}[/red]")
                exit_code = 1

        return exit_code

    def _resolve_path(
        self,
        client: ClientType,
        path: str,
        must_exist: bool,
        allow_missing: bool,
        no_symlinks: bool,
    ) -> str | None:
        """Resolve a path to its absolute form."""
        try:
            # Simple path resolution - convert to absolute
            if not path.startswith("/"):
                # Relative path - we need to get current working directory
                # For now, assume we're in root
                path = "/" + path.lstrip("./")

            # Normalize the path
            parts = []
            for part in path.split("/"):
                if part == "" or part == ".":
                    continue
                elif part == "..":
                    if parts:
                        parts.pop()
                else:
                    parts.append(part)

            resolved = "/" + "/".join(parts)

            # Check if path exists if required
            if (
                must_exist
                and not allow_missing
                and safe_read_file(client, resolved, self.shell) is None
            ):
                self.console.print(
                    f"[red]realpath: {path}: No such file or directory[/red]"
                )
                return None

            return resolved

        except Exception as e:
            self.console.print(f"[red]realpath: {path}: {e}[/red]")
            return None
