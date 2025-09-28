"""Implementation of MktempCommand."""

from __future__ import annotations

import os
import uuid
from io import StringIO
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class MktempCommand(Command):
    """Implementation of mktemp command."""

    name = "mktemp"
    help = "Create temporary files or directories"
    category = "File Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Create temporary files or directories.

Usage: mktemp [OPTIONS] [TEMPLATE]

Description:
    Create a temporary file or directory and print its name.
    TEMPLATE may contain XXXXXX which will be replaced with random characters.

Options:
    -d, --directory Create a directory instead of a file
    -p DIR          Use DIR as prefix for temporary files
    -t              Treat TEMPLATE as a single file component relative to temp dir
    -h, --help      Show this help message

Examples:
    mktemp
    mktemp -d
    mktemp fileXXXXXX.txt
    mktemp -d -t tmpdir.XXXXXX
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the mktemp command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "d": bool,  # create directory
                "directory": bool,
                "p": str,  # prefix directory
                "t": bool,  # template relative to temp dir
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        create_dir = flags.get("d", False) or flags.get("directory", False)
        prefix_dir = flags.get("p", None)
        use_temp_dir = flags.get("t", False)
        template = positional_args[0] if positional_args else None

        try:
            # Determine template and directory
            if use_temp_dir or not template:
                # Use system temp directory
                temp_base = "/tmp"  # noqa: S108
                template_name = template or "tmp.XXXXXX"
            else:
                # Use provided template path
                if "/" in template:
                    temp_base = os.path.dirname(template)
                    template_name = os.path.basename(template)
                else:
                    temp_base = "."
                    template_name = template

            if prefix_dir:
                temp_base = prefix_dir

            # Create the temporary file/directory on the remote system
            # Since we can't directly create temp files on remote, we'll generate a name

            if "XXXXXX" in template_name:
                # Replace XXXXXX with random characters
                random_part = str(uuid.uuid4())[:6]
                final_name = template_name.replace("XXXXXX", random_part)
            else:
                final_name = f"{template_name}.{str(uuid.uuid4())[:6]}"

            full_path = f"{temp_base.rstrip('/')}/{final_name}"

            if create_dir:
                # Create directory
                try:
                    client.make_dir(full_path, make_parents=True)
                    self.console.print(full_path)
                    return 0
                except Exception as e:
                    self.console.print(
                        get_theme().error_text(
                            f"mktemp: cannot create directory {full_path}: {e}"
                        )
                    )
                    return 1
            else:
                # Create file
                try:
                    # Create empty file by pushing empty content
                    empty_content = StringIO("")
                    client.push(full_path, empty_content)
                    self.console.print(full_path)
                    return 0
                except Exception as e:
                    self.console.print(
                        get_theme().error_text(
                            f"mktemp: cannot create file {full_path}: {e}"
                        )
                    )
                    return 1

        except Exception as e:
            self.console.print(get_theme().error_text(f"mktemp: {e}"))
            return 1
