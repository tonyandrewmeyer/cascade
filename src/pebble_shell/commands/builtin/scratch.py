"""Scratch command for Cascade.

This module provides implementation for the scratch command that opens
a temporary editor buffer and pushes the result to the remote container.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import uuid
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ScratchCommand(Command):
    """Open a scratch buffer and push to remote container."""

    name = "scratch"
    help = "Open a scratch buffer in editor and push to remote container"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Open a scratch buffer in editor and push to remote container.

Usage: scratch [OPTIONS]

Options:
    -h, --help          Show this help message
    -e, --extension EXT File extension for the scratch file (default: txt)
    -d, --directory DIR Remote directory to save to (default: /tmp)
    -n, --name NAME     Custom name for the remote file (default: auto-generated)

Opens your $EDITOR (or pico if not set) with an empty buffer. When you
save and close the editor, the content is pushed to a temporary file
on the remote container. The path to the remote file is printed so you
can use it.

Examples:
    scratch                     # Create scratch.txt in /tmp
    scratch -e sh               # Create a .sh file
    scratch -e py -d /app       # Create .py file in /app
    scratch -n config.yaml      # Use specific filename
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the scratch command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "e": str,
                "extension": str,
                "d": str,
                "directory": str,
                "n": str,
                "name": str,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        extension = flags["e"] or flags["extension"] or "txt"
        remote_dir = flags["d"] or flags["directory"] or "/tmp"
        custom_name = flags["n"] or flags["name"]

        # Generate remote filename
        if custom_name:
            remote_filename = custom_name
        else:
            random_suffix = str(uuid.uuid4())[:8]
            remote_filename = f"scratch-{random_suffix}.{extension}"

        remote_path = f"{remote_dir.rstrip('/')}/{remote_filename}"

        # Create local temp file with the same extension for editor syntax highlighting
        suffix = f".{extension}" if not extension.startswith(".") else extension
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False
        ) as tmp:
            tmp_path = tmp.name
            # Write nothing - start with empty buffer

        try:
            editor = os.environ.get("EDITOR", "pico")
            before_mtime = os.stat(tmp_path).st_mtime

            # Open editor
            self.console.print(f"[dim]Opening editor... (will save to {remote_path})[/dim]")
            subprocess.run([editor, tmp_path], check=True)  # noqa: S603

            after_mtime = os.stat(tmp_path).st_mtime

            # Check if file was modified (has content)
            file_size = os.path.getsize(tmp_path)

            if after_mtime == before_mtime and file_size == 0:
                self.console.print("[yellow]scratch: no content written, nothing saved[/yellow]")
                return 1

            # Push to remote
            with open(tmp_path, "rb") as f:
                client.push(remote_path, f, make_dirs=True)

            self.console.print(f"[green]Saved to:[/green] {remote_path}")
            return 0

        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]scratch: editor failed: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]scratch: failed to save: {e}[/red]")
            return 1
        finally:
            # Clean up local temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
