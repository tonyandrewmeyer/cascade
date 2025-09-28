"""Integration tests for the DmesgCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DmesgCommand instance."""
    yield pebble_shell.commands.DmesgCommand(shell=shell)


def test_name(command: pebble_shell.commands.DmesgCommand):
    assert command.name == "dmesg"


def test_category(command: pebble_shell.commands.DmesgCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.DmesgCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "kernel ring buffer" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DmesgCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "kernel ring buffer" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DmesgCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should fail since dmesg access requires special permissions
    assert result == 1
