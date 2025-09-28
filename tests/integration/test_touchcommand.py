"""Integration tests for the TouchCommand."""

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
    """Fixture to create a TouchCommand instance."""
    yield pebble_shell.commands.TouchCommand(shell=shell)


def test_name(command: pebble_shell.commands.TouchCommand):
    assert command.name == "touch <file1> [file2...]"


def test_category(command: pebble_shell.commands.TouchCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.TouchCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Create empty files or update timestamps" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TouchCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Create empty files or update timestamps" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TouchCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: touch" in capture.get()


def test_execute_create_tmp_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TouchCommand,
    tmp_path: pathlib.Path,
):
    new_file = tmp_path / "test_touch.txt"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(new_file)])
    assert result == 0
