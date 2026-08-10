"""JSON format command for Cascade.

This module provides implementation for the jsonformat command that
pretty-prints JSON data.
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class JsonformatCommand(Command):
    """Pretty-print JSON data."""

    name = "jsonformat"
    help = "Pretty-print JSON data"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Pretty-print JSON data.

Usage: jsonformat [OPTIONS] [JSON_STRING]
       echo '{"key":"value"}' | jsonformat

Options:
    -h, --help          Show this help message
    -i, --indent N      Indentation level (default: 2)
    -c, --compact       Output compact JSON (no formatting)
    -s, --sort-keys     Sort object keys alphabetically

If no JSON_STRING is provided, reads from stdin.

Examples:
    jsonformat '{"name":"John","age":30}'
    echo '{"a":1,"b":2}' | jsonformat
    jsonformat -i 4 '{"nested":{"key":"value"}}'
    jsonformat -c '{"key": "value"}'
    jsonformat -s '{"z":1,"a":2}'
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the jsonformat command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "i": int,
                "indent": int,
                "c": bool,
                "compact": bool,
                "s": bool,
                "sort-keys": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        compact = flags["c"] or flags["compact"]
        sort_keys = flags["s"] or flags["sort-keys"]
        indent = flags["i"] or flags["indent"] or 2

        if compact:
            indent = None
            separators = (',', ':')
        else:
            separators = None

        # Get JSON input
        if positional_args:
            json_str = ' '.join(positional_args)
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                json_str = sys.stdin.read()
            else:
                self.console.print("[yellow]jsonformat: no input provided[/yellow]")
                return 1

        try:
            data = json.loads(json_str)
            formatted = json.dumps(
                data,
                indent=indent,
                sort_keys=sort_keys,
                separators=separators,
                ensure_ascii=False
            )
            self.console.print(formatted)
            return 0
        except json.JSONDecodeError as e:
            self.console.print(f"[red]jsonformat: invalid JSON: {e}[/red]")
            return 1
