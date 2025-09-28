"""Integration tests for the RemoveDirCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RemoveDirCommand instance."""
    yield pebble_shell.commands.RemoveDirCommand(shell=shell)


def test_name(command: pebble_shell.commands.RemoveDirCommand):
    assert command.name == "rmdir <directory1> [directory2...]"


def test_category(command: pebble_shell.commands.RemoveDirCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.RemoveDirCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Remove empty directories" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveDirCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Remove empty directories" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveDirCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    assert "Usage: rmdir" in output and "directory" in output


def test_execute_remove_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveDirCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/directory"])
    assert result == 1
