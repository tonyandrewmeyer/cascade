"""Implementation of EditCommand."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING, Union

import ops
from rich.panel import Panel

from ...utils.command_helpers import handle_help_flag
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class EditCommand(Command):
    """Command for editing remote files locally with automatic sync."""
    name = "edit"
    help = "Edit a remote file locally and push changes back. Usage: edit REMOTE_PATH"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the edit command to edit a remote file locally."""
        if handle_help_flag(self, args):
            return 0
        console = self.console
        if not args:
            console.print(
                Panel(
                    "No remote file specified.",
                    title="[b red]edit Error[/b red]",
                    style="red",
                )
            )
            return 1
        remote_path = args[0]
        cwd = self.shell.current_directory
        if not os.path.isabs(remote_path):
            remote_path = os.path.normpath(os.path.join(cwd, remote_path))
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp:
            tmp_path = tmp.name
            with client.pull(remote_path, encoding=None) as remote_f:
                assert isinstance(remote_f, bytes)
                shutil.copyfileobj(io.BytesIO(remote_f), tmp)
        editor = os.environ.get("EDITOR", "pico")
        before = os.stat(tmp_path).st_mtime
        subprocess.run([editor, tmp_path], check=True)
        after = os.stat(tmp_path).st_mtime
        if after != before:
            with open(tmp_path, "rb") as f:
                client.push(remote_path, f)
            console.print(
                Panel(
                    f"[green]Saved changes to {remote_path}[/green]",
                    title="[b]edit[/b]",
                    style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[yellow]No changes made to {remote_path}[/yellow]",
                    title="[b]edit[/b]",
                    style="yellow",
                )
            )
        return 0
