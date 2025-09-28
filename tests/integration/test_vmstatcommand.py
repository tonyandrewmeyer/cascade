"""Integration tests for the VmstatCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a VmstatCommand instance."""
    yield pebble_shell.commands.VmstatCommand(shell=shell)


def test_name(command: pebble_shell.commands.VmstatCommand):
    assert command.name == "vmstat [interval] [count]"


def test_category(command: pebble_shell.commands.VmstatCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.VmstatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "virtual memory statistics" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VmstatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "virtual memory" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VmstatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should show vmstat information
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_with_invalid_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.VmstatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["invalid"])
    # Should fail with invalid interval
    assert result == 1
