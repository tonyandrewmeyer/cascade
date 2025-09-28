"""Implementation of MarkdownCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Probably this would be better in the text category?
class MarkdownCommand(Command):
    """Command for pretty-printing Markdown files with formatting."""
    name = "md"
    help = "Pretty-print Markdown files with syntax highlighting and formatting"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the markdown command to format and display Markdown files."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print(
                Panel(
                    "No file specified. Usage: md <file>",
                    title="[b red]md Error[/b red]",
                    style="red",
                )
            )
            return 1

        file_path = args[0]
        cwd = self.shell.current_directory

        # Resolve path
        if not os.path.isabs(file_path):
            file_path = os.path.normpath(os.path.join(cwd, file_path))

        try:
            with client.pull(file_path) as file:
                content = file.read()

                if isinstance(content, bytes):
                    try:
                        content = content.decode("utf-8")
                    except UnicodeDecodeError:
                        self.console.print(
                            Panel(
                                f"Error: {file_path} contains binary data or is not UTF-8 encoded",
                                title="[b red]md Error[/b red]",
                                style="red",
                            )
                        )
                        return 1

                # Create Markdown object with Rich
                md = Markdown(
                    content,
                    code_theme="monokai",  # Nice syntax highlighting
                    justify="left",
                )

                # Print the formatted markdown
                self.console.print(md)

        except Exception as e:
            self.console.print(
                Panel(
                    f"Error reading file {file_path}: {e}",
                    title="[b red]md Error[/b red]",
                    style="red",
                )
            )
            return 1

        return 0
