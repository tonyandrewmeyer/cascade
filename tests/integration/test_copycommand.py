"""Integration tests for the CopyCommand."""

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
    """Fixture to create a CopyCommand instance."""
    yield pebble_shell.commands.CopyCommand(shell=shell)


def test_name(command: pebble_shell.commands.CopyCommand):
    assert command.name == "cp"


def test_category(command: pebble_shell.commands.CopyCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.CopyCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Copy files and directories" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CopyCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Copy files and directories" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CopyCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: cp [-r] <source> <destination>" in capture.get()


def test_execute_copy_to_tmp(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CopyCommand,
    tmp_path: pathlib.Path,
):
    tmp_dest = tmp_path / "test_copy"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", str(tmp_dest)])
    # Should succeed copying /etc/passwd to tmp directory
    assert result == 0


def test_execute_copy_nonexistent_source(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CopyCommand,
    tmp_path: pathlib.Path,
):
    tmp_dest = tmp_path / "test_copy"
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["/nonexistent/file", str(tmp_dest)]
        )
    assert result == 1
