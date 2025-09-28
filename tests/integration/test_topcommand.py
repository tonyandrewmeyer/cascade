"""Integration tests for the TopCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TopCommand instance."""
    yield pebble_shell.commands.TopCommand(shell=shell)


def test_name(command: pebble_shell.commands.TopCommand):
    assert command.name == "top"


def test_category(command: pebble_shell.commands.TopCommand):
    assert command.category == "System Commands"


def test_help(command: pebble_shell.commands.TopCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display system processes in a top-like interface" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TopCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display system processes in a top-like interface" in capture.get()


def test_execute_batch_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TopCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-b", "-n", "1"])
    assert result == 0
