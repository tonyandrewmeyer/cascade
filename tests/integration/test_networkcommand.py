"""Integration tests for the NetworkCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NetworkCommand instance."""
    yield pebble_shell.commands.NetworkCommand(shell=shell)


def test_name(command: pebble_shell.commands.NetworkCommand):
    assert command.name == "net"


def test_category(command: pebble_shell.commands.NetworkCommand):
    assert command.category == "Network Commands"


def test_help(command: pebble_shell.commands.NetworkCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show network interface statistics" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NetworkCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show network interface statistics" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NetworkCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0
