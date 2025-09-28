"""Integration tests for the FalseCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FalseCommand instance."""
    yield pebble_shell.commands.FalseCommand(shell=shell)


def test_name(command: pebble_shell.commands.FalseCommand):
    assert command.name == "false"


def test_category(command: pebble_shell.commands.FalseCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.FalseCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Exit with failure (exit code 1)" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FalseCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Exit with failure (exit code 1)" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FalseCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FalseCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["any", "args", "ignored"])
    assert result == 1
