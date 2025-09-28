"""Integration tests for the FreeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FreeCommand instance."""
    yield pebble_shell.commands.FreeCommand(shell=shell)


def test_name(command: pebble_shell.commands.FreeCommand):
    assert command.name == "free"


def test_category(command: pebble_shell.commands.FreeCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.FreeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display memory usage" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FreeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display memory usage" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FreeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should fail since /proc/meminfo is not available in container
    assert result == 1


def test_execute_human_readable(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FreeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-h"])
    # Should fail since /proc/meminfo is not available in container
    assert result == 1
