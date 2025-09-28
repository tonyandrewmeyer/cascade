"""Integration tests for the RunCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RunCommand instance."""
    yield pebble_shell.commands.RunCommand(shell=shell)


def test_name(command: pebble_shell.commands.RunCommand):
    assert command.name == "run <command> [args...]"


def test_category(command: pebble_shell.commands.RunCommand):
    assert command.category == "Remote Execution"


def test_help(command: pebble_shell.commands.RunCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Run a command on the remote system" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Run a command on the remote system" in capture.get()


def test_execute_basic_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["echo", "test"])
    output = capture.get()
    # Should succeed executing echo command
    assert result == 0
    # Should have the test output
    assert "test" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    assert "Usage: run" in output
