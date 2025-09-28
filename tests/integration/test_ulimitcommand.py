"""Integration tests for the UlimitCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an UlimitCommand instance."""
    yield pebble_shell.commands.UlimitCommand(shell=shell)


def test_name(command: pebble_shell.commands.UlimitCommand):
    assert command.name == "ulimit [-a] [-option]"


def test_category(command: pebble_shell.commands.UlimitCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.UlimitCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show resource limits" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UlimitCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show resource limits" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UlimitCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should succeed reading process limits
    assert result == 0


def test_execute_show_all(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UlimitCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-a"])
    # Should succeed showing all limits
    assert result == 0


def test_execute_invalid_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UlimitCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid"])
    assert result == 1
    assert "Usage: ulimit" in capture.get()
