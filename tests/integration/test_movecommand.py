"""Integration tests for the MoveCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import pathlib

    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MoveCommand instance."""
    yield pebble_shell.commands.MoveCommand(shell=shell)


def test_name(command: pebble_shell.commands.MoveCommand):
    assert command.name == "mv"


def test_category(command: pebble_shell.commands.MoveCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.MoveCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Move/rename files or directories" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoveCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Move/rename files or directories" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoveCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: mv <source> <destination>" in capture.get()


def test_execute_move_nonexistent_source(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoveCommand,
    tmp_path: pathlib.Path,
):
    tmp_dest = tmp_path / "test_move"
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["/nonexistent/file", str(tmp_dest)]
        )
    assert result == 1
