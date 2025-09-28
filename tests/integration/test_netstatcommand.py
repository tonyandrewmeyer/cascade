"""Integration tests for the NetstatCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NetstatCommand instance."""
    yield pebble_shell.commands.NetstatCommand(shell=shell)


def test_name(command: pebble_shell.commands.NetstatCommand):
    assert command.name == "netstat"


def test_category(command: pebble_shell.commands.NetstatCommand):
    assert command.category == "Network Commands"


def test_help(command: pebble_shell.commands.NetstatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show network connections" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NetstatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show network connections" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NetstatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_with_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NetstatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-t"])
    assert result == 0
