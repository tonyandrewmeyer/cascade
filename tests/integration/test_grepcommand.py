"""Integration tests for the GrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a GrepCommand instance."""
    yield pebble_shell.commands.GrepCommand(shell=shell)


def test_name(command: pebble_shell.commands.GrepCommand):
    assert command.name == "grep <pattern> <file> [file2...]"


def test_category(command: pebble_shell.commands.GrepCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.GrepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Search for pattern in files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GrepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Search for pattern in files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GrepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: grep <pattern> <file>" in capture.get()


def test_execute_insufficient_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GrepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["pattern"])
    assert result == 1
    assert "Usage: grep <pattern> <file>" in capture.get()


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GrepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["pattern", "/nonexistent/file"])
    # Should fail because file doesn't exist
    assert result == 1
