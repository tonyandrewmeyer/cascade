"""Integration tests for the InfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an InfoCommand instance."""
    yield pebble_shell.commands.InfoCommand(shell=shell)


def test_name(command: pebble_shell.commands.InfoCommand):
    assert command.name == "info"


def test_category(command: pebble_shell.commands.InfoCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.InfoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show system information" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.InfoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show system information" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.InfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    output = capture.get()
    assert "Cascade System Information" in output
    assert "Shell Information" in output
    assert "Current Directory" in output
    assert "Use 'help' to see all shell features" in output
