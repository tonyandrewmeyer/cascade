"""Integration tests for the WatchCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WatchCommand instance."""
    yield pebble_shell.commands.WatchCommand(shell=shell)


def test_name(command: pebble_shell.commands.WatchCommand):
    assert command.name == "watch [-n seconds] <command>"


def test_category(command: pebble_shell.commands.WatchCommand):
    assert command.category == "Remote Execution"


def test_help(command: pebble_shell.commands.WatchCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Execute a command repeatedly" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WatchCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Execute a command repeatedly" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WatchCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: watch [-n seconds] <command>" in capture.get()


def test_execute_invalid_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WatchCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "invalid", "echo", "test"])
    assert result == 1
    assert "Error: interval must be a number" in capture.get()


def test_execute_no_command_after_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WatchCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "1"])
    assert result == 1
    assert "Error: no command specified" in capture.get()
