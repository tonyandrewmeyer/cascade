"""Integration tests for the RemoveCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RemoveCommand instance."""
    yield pebble_shell.commands.RemoveCommand(shell=shell)


def test_name(command: pebble_shell.commands.RemoveCommand):
    assert command.name == "rm [-r] [-f] <file1> [file2...]"


def test_category(command: pebble_shell.commands.RemoveCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.RemoveCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Remove files and directories" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Remove files and directories" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    assert "Usage: rm [-r] [-f]" in output and "file" in output


def test_execute_remove_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RemoveCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    assert result == 1
