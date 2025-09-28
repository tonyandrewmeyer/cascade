"""Integration tests for the DiffCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DiffCommand instance."""
    yield pebble_shell.commands.DiffCommand(shell=shell)


def test_name(command: pebble_shell.commands.DiffCommand):
    assert command.name == "diff"


def test_category(command: pebble_shell.commands.DiffCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.DiffCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compare files line by line" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DiffCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Compare files line by line" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DiffCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: diff [-r] file1 file2" in capture.get()


def test_execute_same_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DiffCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "/etc/passwd"])
    # Same file should have no differences
    assert result == 0  # Same file should have no differences


def test_execute_nonexistent_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DiffCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent1", "/nonexistent2"])
    assert result == 1
