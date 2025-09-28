"""Implementation of YqCommand."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any, Union, cast

import ops
import yaml
from rich.panel import Panel
from rich.syntax import Syntax

from ...utils import resolve_path
from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class YqCommand(Command):
    """Command for pretty-printing YAML files with optional keypath filtering."""

    name = "yq"
    help = "Pretty-print YAML files with optional jq-like keypath filtering. Usage: yq <file> [.foo.bar]"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the yq command to format and filter YAML files."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print(
                Panel(
                    "No file specified. Usage: yq <file> [.foo.bar]",
                    title="[b red]yq Error[/b red]",
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
                        title="[b red]yq Error[/b red]",
                        style="red",
                    )
                )
                return 1

        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except Exception as e:
            self.console.print(
                Panel(
                    f"Error parsing YAML: {e}",
                    title="[b red]yq Error[/b red]",
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
                            title="[b red]yq Error[/b red]",
                            style="red",
                        )
                    )
                    return 1
            else:
                self.console.print(
                    Panel(
                        f"Invalid keypath: {keypath}. Must start with a dot (e.g., .foo.bar)",
                        title="[b red]yq Error[/b red]",
                        style="red",
                    )
                )
                return 1

        # Pretty-print YAML with syntax highlighting
        yaml_str = yaml.safe_dump(
            data,
            default_flow_style=False,
            indent=2,
            sort_keys=False,
            allow_unicode=True,
        )
        syntax = Syntax(
            yaml_str,
            "yaml",
            theme="monokai",
            word_wrap=True,
            line_numbers=True,
            background_color="default",
        )
        self.console.print(
            Panel(
                syntax,
                title="[b]yq Output[/b]",
                style="cyan",
                border_style="bright_blue",
            )
        )
        return 0
