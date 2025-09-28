"""Integration tests for the LsofCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an LsofCommand instance."""
    yield pebble_shell.commands.LsofCommand(shell=shell)


def test_name(command: pebble_shell.commands.LsofCommand):
    assert command.name == "lsof"


def test_category(command: pebble_shell.commands.LsofCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.LsofCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "List open files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsofCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "List open files" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsofCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should fail since /proc filesystem may not be fully available
    assert result == 1
