"""Implementation of JqCommand."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any, Union, cast

import ops
from rich.panel import Panel
from rich.syntax import Syntax

from ...utils import resolve_path
from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class JqCommand(Command):
    name = "jq"
    help = "Pretty-print JSON files with optional jq-like keypath filtering. Usage: jq <file> [.foo.bar]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print(
                Panel(
                    "No file specified. Usage: jq <file> [.foo.bar]",
                    title="[b red]jq Error[/b red]",
                    style="red",
                )
            )
            return 1

        file_path = args[0]
        keypath = args[1] if len(args) > 1 else None
        cwd = self.shell.current_directory

        # Resolve path
        if file_path == "-":
            # Read from stdin
            content = sys.stdin.read()
        else:
            if not os.path.isabs(file_path):
                file_path = os.path.normpath(os.path.join(cwd, file_path))
            try:
                resolved_path = resolve_path(cwd, file_path, self.shell.home_dir)
                with client.pull(resolved_path) as file:
                    content = file.read()
                    if isinstance(content, bytes):
                        content = content.decode("utf-8")
            except Exception as e:
                self.console.print(
                    Panel(
                        f"Error reading file {file_path}: {e}",
                        title="[b red]jq Error[/b red]",
                        style="red",
                    )
                )
                return 1

        # Parse JSON
        try:
            data = json.loads(content)
        except Exception as e:
            self.console.print(
                Panel(
                    f"Error parsing JSON: {e}",
                    title="[b red]jq Error[/b red]",
                    style="red",
                )
            )
            return 1

        # Apply keypath filter if provided
        if keypath:
            if keypath.startswith("."):
                keys = [k for k in keypath.lstrip(".").split(".") if k]
                try:
                    for k in keys:
                        if isinstance(data, dict):
                            data = cast("dict[Any, Any]", data)
                            data = data[k]
                        elif isinstance(data, list) and k.isdigit():
                            data = cast("list[Any]", data)
                            data = data[int(k)]
                        else:
                            raise KeyError(k)
                except Exception as e:
                    self.console.print(
                        Panel(
                            f"Key path error: {e}",
                            title="[b red]jq Error[/b red]",
                            style="red",
                        )
                    )
                    return 1
            else:
                self.console.print(
                    Panel(
                        f"Invalid keypath: {keypath}. Must start with a dot (e.g., .foo.bar)",
                        title="[b red]jq Error[/b red]",
                        style="red",
                    )
                )
                return 1

        # Pretty-print JSON with syntax highlighting
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(
            json_str,
            "json",
            theme="monokai",
            word_wrap=True,
            line_numbers=True,
            background_color="default",
        )
        self.console.print(
            Panel(
                syntax,
                title="[b]jq Output[/b]",
                style="cyan",
                border_style="bright_blue",
            )
        )
        return 0
