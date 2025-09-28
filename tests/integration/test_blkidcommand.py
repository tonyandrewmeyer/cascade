"""Integration tests for the BlkidCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a BlkidCommand instance."""
    yield pebble_shell.commands.BlkidCommand(shell=shell)


def test_name(command: pebble_shell.commands.BlkidCommand):
    assert command.name == "blkid"


def test_category(command: pebble_shell.commands.BlkidCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.BlkidCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "block device" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BlkidCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "block device" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BlkidCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should fail since no block devices available in container
    assert result == 1


def test_execute_specific_device(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BlkidCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/dev/sda1"])
    # Should fail since /dev/sda1 doesn't exist in container
    assert result == 1
