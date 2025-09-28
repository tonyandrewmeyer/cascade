"""Integration tests for the BzcatCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a BzcatCommand instance."""
    yield pebble_shell.commands.BzcatCommand(shell=shell)


def test_name(command: pebble_shell.commands.BzcatCommand):
    assert command.name == "bzcat"


def test_category(command: pebble_shell.commands.BzcatCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.BzcatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Decompress and print .bz2 files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BzcatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Decompress and print .bz2 files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BzcatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: bzcat file" in capture.get()


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.BzcatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.bz2"])
    # Should fail because file doesn't exist
    assert result == 1
