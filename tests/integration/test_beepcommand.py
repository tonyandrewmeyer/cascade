"""Integration tests for the BeepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a BeepCommand instance."""
    yield pebble_shell.commands.BeepCommand(shell=shell)


def test_name(command: pebble_shell.commands.BeepCommand):
    assert command.name == "beep"


def test_category(command: pebble_shell.commands.BeepCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.BeepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Play a beep sound" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BeepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Play a beep sound" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BeepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BeepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["any", "args", "ignored"])
    assert result == 0
