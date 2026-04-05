"""Serveit command for Cascade.

This module provides implementation for the serveit command that starts
a simple HTTP server to serve files from the local directory.
"""

from __future__ import annotations

import os
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that can optionally suppress logging."""

    quiet = False

    def log_message(self, format, *args):
        """Log an arbitrary message, unless quiet mode is enabled."""
        if not self.quiet:
            super().log_message(format, *args)


class ServeitCommand(Command):
    """Start a simple HTTP server to serve local files."""

    name = "serveit"
    help = "Start a simple HTTP server to serve local files"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Start a simple HTTP server to serve local files.

Usage: serveit [OPTIONS] [PORT]

Options:
    -h, --help          Show this help message
    -d, --directory DIR Serve files from DIR (default: current local directory)
    -q, --quiet         Suppress request logging
    -b, --background    Run server in background (non-blocking)

Arguments:
    PORT                Port to listen on (default: 8000)

Starts a simple HTTP file server on localhost. This serves files from your
LOCAL machine, not the remote container. Useful for making files available
to containers or for quick file sharing.

Press Ctrl+C to stop the server (unless running in background).

Examples:
    serveit                 # Serve current directory on port 8000
    serveit 3000            # Serve on port 3000
    serveit -d /tmp/files   # Serve specific directory
    serveit -q 8080         # Quiet mode on port 8080
    serveit -b              # Run in background
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the serveit command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "d": str,
                "directory": str,
                "q": bool,
                "quiet": bool,
                "b": bool,
                "background": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        # Parse port
        port = 8000
        if positional_args:
            try:
                port = int(positional_args[0])
                if port < 1 or port > 65535:
                    raise ValueError("Port out of range")
            except ValueError:
                self.console.print(f"[red]serveit: invalid port: {positional_args[0]}[/red]")
                return 1

        # Get directory to serve
        directory = flags["d"] or flags["directory"] or os.getcwd()
        if not os.path.isdir(directory):
            self.console.print(f"[red]serveit: not a directory: {directory}[/red]")
            return 1

        quiet = flags["q"] or flags["quiet"]
        background = flags["b"] or flags["background"]

        # Create handler class with the directory
        handler_class = partial(QuietHTTPRequestHandler, directory=directory)
        handler_class.quiet = quiet

        try:
            server = HTTPServer(("localhost", port), handler_class)
        except OSError as e:
            if "Address already in use" in str(e) or "address already in use" in str(e).lower():
                self.console.print(f"[red]serveit: port {port} is already in use[/red]")
            else:
                self.console.print(f"[red]serveit: failed to start server: {e}[/red]")
            return 1

        self.console.print(f"[green]Serving[/green] [cyan]{directory}[/cyan]")
        self.console.print(f"[green]URL:[/green] [link=http://localhost:{port}]http://localhost:{port}[/link]")

        if background:
            self.console.print("[dim]Running in background. Server will stop when Cascade exits.[/dim]")
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            return 0
        else:
            self.console.print("[dim]Press Ctrl+C to stop[/dim]")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Server stopped[/yellow]")
                server.shutdown()
            return 0
