"""URL parsing command for Cascade.

This module provides implementation for the url command that parses
URLs and displays their components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union
from urllib.parse import parse_qsl, urlparse

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UrlCommand(Command):
    """Parse a URL and display its components."""

    name = "url"
    help = "Parse a URL and display its components"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Parse a URL and display its components.

Usage: url [OPTIONS] URL

Options:
    -h, --help      Show this help message
    -q, --quiet     Only show non-empty components
    -j, --json      Output as JSON

Parses a URL and displays its components: protocol, hostname, port,
path, query parameters, and fragment.

Examples:
    url https://example.com/path?foo=bar#section
    url -q "http://user:pass@host:8080/path"
    url --json "https://api.example.com/v1/users?id=123"
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the url command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "q": bool,
                "quiet": bool,
                "j": bool,
                "json": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not positional_args:
            self.console.print("[red]url: missing URL argument[/red]")
            return 1

        url = positional_args[0]
        quiet = flags["q"] or flags["quiet"]
        as_json = flags["j"] or flags["json"]

        try:
            parsed = urlparse(url)
        except Exception as e:
            self.console.print(f"[red]url: failed to parse URL: {e}[/red]")
            return 1

        if as_json:
            self._output_json(url, parsed)
        else:
            self._output_text(url, parsed, quiet)

        return 0

    def _output_text(self, original: str, parsed, quiet: bool):
        """Output URL components as text."""
        self.console.print(f"[cyan]original:[/cyan] {original}")

        if parsed.scheme or not quiet:
            self.console.print(f"[cyan]protocol:[/cyan] {parsed.scheme or '(none)'}")

        if parsed.username is not None:
            self.console.print(f"[cyan]username:[/cyan] {parsed.username}")
        elif not quiet:
            pass  # Don't show empty username

        if parsed.password is not None:
            self.console.print(f"[cyan]password:[/cyan] {parsed.password}")

        if parsed.hostname is not None:
            self.console.print(f"[cyan]hostname:[/cyan] {parsed.hostname}")
        elif not quiet:
            self.console.print("[cyan]hostname:[/cyan] (none)")

        if parsed.port is not None:
            self.console.print(f"[cyan]port:[/cyan] {parsed.port}")

        if len(parsed.path) != 0:
            self.console.print(f"[cyan]path:[/cyan] {parsed.path}")
        elif not quiet:
            self.console.print("[cyan]path:[/cyan] (none)")

        if len(parsed.query) != 0:
            self.console.print(f"[cyan]query:[/cyan] {parsed.query}")
            for key, value in parse_qsl(parsed.query):
                self.console.print(f"  [dim]-[/dim] [yellow]{key}[/yellow] = {value}")

        if len(parsed.fragment) != 0:
            self.console.print(f"[cyan]hash:[/cyan] {parsed.fragment}")

    def _output_json(self, original: str, parsed):
        """Output URL components as JSON."""
        import json

        data = {
            "original": original,
            "protocol": parsed.scheme or None,
            "username": parsed.username,
            "password": parsed.password,
            "hostname": parsed.hostname,
            "port": parsed.port,
            "path": parsed.path or None,
            "query": parsed.query or None,
            "query_params": dict(parse_qsl(parsed.query)) if parsed.query else None,
            "hash": parsed.fragment or None,
        }

        # Remove None values for cleaner output
        data = {k: v for k, v in data.items() if v is not None}

        self.console.print(json.dumps(data, indent=2))
