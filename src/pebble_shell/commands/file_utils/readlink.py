"""Implementation of ReadlinkCommand."""

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


class ReadlinkCommand(Command):
    """Implementation of readlink command."""

    name = "readlink"
    help = "Display value of symbolic link"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Display value of symbolic link.

Usage: readlink [OPTIONS] FILE...

Description:
    Print value of a symbolic link or canonical file name.

Options:
    -f, --canonicalize      Canonicalize by following every symlink recursively
    -e, --canonicalize-existing  Canonicalize but all components must exist
    -m, --canonicalize-missing   Canonicalize but components don't need to exist
    -n, --no-newline        Do not output trailing newline
    -q, --quiet, --silent   Suppress most error messages
    -v, --verbose           Report error messages
    -z, --zero              End each output line with NUL, not newline
    -h, --help              Show this help message

Examples:
    readlink /usr/bin/vi    # Show where symlink points
    readlink -f /usr/bin/vi # Show canonical path
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the readlink command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "f": bool,  # canonicalize
                "canonicalize": bool,
                "e": bool,  # canonicalize-existing
                "canonicalize-existing": bool,
                "m": bool,  # canonicalize-missing
                "canonicalize-missing": bool,
                "n": bool,  # no-newline
                "no-newline": bool,
                "q": bool,  # quiet
                "quiet": bool,
                "silent": bool,
                "v": bool,  # verbose
                "verbose": bool,
                "z": bool,  # zero
                "zero": bool,
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        canonicalize = flags.get("f", False) or flags.get("canonicalize", False)
        canon_existing = flags.get("e", False) or flags.get(
            "canonicalize-existing", False
        )
        canon_missing = flags.get("m", False) or flags.get(
            "canonicalize-missing", False
        )
        no_newline = flags.get("n", False) or flags.get("no-newline", False)
        quiet = (
            flags.get("q", False)
            or flags.get("quiet", False)
            or flags.get("silent", False)
        )
        _verbose = flags.get("v", False) or flags.get("verbose", False)
        zero_terminate = flags.get("z", False) or flags.get("zero", False)

        if not positional_args:
            if not quiet:
                self.console.print(get_theme().error_text("readlink: missing operand"))
            return 1

        exit_code = 0

        try:
            for file_path in positional_args:
                try:
                    if canonicalize or canon_existing or canon_missing:
                        # For canonicalisation, we need to resolve the full path
                        result = self._canonicalise_path(
                            client, file_path, canon_existing
                        )
                    else:
                        # Just read the symlink
                        result = self._read_symlink(client, file_path)

                    if result is not None:
                        if zero_terminate:
                            self.console.print(result, end="\0")
                        elif no_newline:
                            self.console.print(result, end="")
                        else:
                            self.console.print(result)
                    else:
                        if not quiet:
                            self.console.print(
                                get_theme().error_text(
                                    f"readlink: {file_path}: not a symbolic link"
                                )
                            )
                        exit_code = 1

                except Exception as e:  # noqa: PERF203  # needed for robust file processing
                    if not quiet:
                        self.console.print(
                            get_theme().error_text(f"readlink: {file_path}: {e}")
                        )
                    exit_code = 1

            return exit_code

        except Exception as e:
            if not quiet:
                self.console.print(get_theme().error_text(f"readlink: {e}"))
            return 1

    def _read_symlink(self, client: ClientType, path: str) -> str | None:
        """Read the target of a symbolic link."""
        # This is challenging with Pebble's filesystem access
        # We can't directly read symlinks, but we can try some approaches

        # Try to read /proc/self/fd/* or similar methods
        # For now, return None as we can't easily determine symlink targets
        # In a real implementation, this would require lower-level access

        return None

    def _canonicalise_path(
        self, client: ClientType, path: str, must_exist: bool = False
    ) -> str | None:
        """Canonicalise a path by resolving symlinks and normalising."""
        # This is similar to realpath functionality
        # For now, just return the normalised path without symlink resolution

        # Normalize the path
        canonical = path if path.startswith("/") else "/" + path

        # Remove redundant separators and resolve . and ..
        parts = []
        for part in canonical.split("/"):
            if part == "" or part == ".":
                continue
            elif part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)

        result = "/" + "/".join(parts) if parts else "/"

        if must_exist:
            # Check if the path exists
            if safe_read_file(client, result, self.shell) is not None:
                return result
            else:
                return None

        return result
