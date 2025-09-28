"""Integration tests for the ExecCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an ExecCommand instance."""
    yield pebble_shell.commands.ExecCommand(shell=shell)


def test_name(command: pebble_shell.commands.ExecCommand):
    assert command.name == "exec <command> [args...]"


def test_category(command: pebble_shell.commands.ExecCommand):
    assert command.category == "Remote Execution"


def test_help(command: pebble_shell.commands.ExecCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Execute commands remotely" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ExecCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Execute commands remotely" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ExecCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    assert "Usage: exec <command>" in capture.get()


def test_execute_basic_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ExecCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["nonexistent-cmd", "echo", "test"]
        )
    # Command doesn't exist so this should fail.
    assert result == 1
    assert "Command failed:" in capture.get()
