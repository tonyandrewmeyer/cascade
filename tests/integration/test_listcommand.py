"""Integration tests for the ListCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ListCommand instance."""
    yield pebble_shell.commands.ListCommand(shell=shell)


def test_name(command: pebble_shell.commands.ListCommand):
    assert command.name == "ls"


def test_category(command: pebble_shell.commands.ListCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.ListCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "List directory contents" in capture.get()


@pytest.mark.parametrize("args", [["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "List directory contents" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_root_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/"])
    assert result == 0


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent"])
    assert result == 1
