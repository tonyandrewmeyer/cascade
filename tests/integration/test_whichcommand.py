"""Integration tests for the WhichCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WhichCommand instance."""
    yield pebble_shell.commands.WhichCommand(shell=shell)


def test_name(command: pebble_shell.commands.WhichCommand):
    assert command.name == "which <command> [command2...]"


def test_category(command: pebble_shell.commands.WhichCommand):
    assert command.category == "Remote Execution"


def test_help(command: pebble_shell.commands.WhichCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Find the location of a command on the remote system" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhichCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Find the location of a command on the remote system" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhichCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: which <command>" in capture.get()


def test_execute_find_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhichCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["sh"])
    # Should find sh in PATH since it's a standard command
    assert result == 0
    output = capture.get()
    assert "sh" in output


def test_execute_nonexistent_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhichCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistentcommand123"])
    assert result == 1
    output = capture.get()
    assert "not found" in output
