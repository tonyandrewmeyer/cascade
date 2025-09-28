"""Integration tests for the MakeDirCommand."""

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
    """Fixture to create a MakeDirCommand instance."""
    yield pebble_shell.commands.MakeDirCommand(shell=shell)


def test_name(command: pebble_shell.commands.MakeDirCommand):
    assert command.name == "mkdir [-p] <directory1> [directory2...]"


def test_category(command: pebble_shell.commands.MakeDirCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.MakeDirCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Create directories" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakeDirCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Create directories" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakeDirCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    assert "Usage: mkdir [-p]" in output and "directory" in output


def test_execute_create_tmp_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakeDirCommand,
    tmp_path: pathlib.Path,
):
    new_dir = tmp_path / "test_mkdir"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(new_dir)])
    assert result == 0


def test_execute_create_nested_directories(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MakeDirCommand,
    tmp_path: pathlib.Path,
):
    nested_dir = tmp_path / "parent" / "child"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-p", str(nested_dir)])
    assert result == 0
