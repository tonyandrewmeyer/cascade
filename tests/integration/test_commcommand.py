"""Integration tests for the CommCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CommCommand instance."""
    yield pebble_shell.commands.CommCommand(shell=shell)


def test_name(command: pebble_shell.commands.CommCommand):
    assert command.name == "comm"


def test_category(command: pebble_shell.commands.CommCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.CommCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compare two sorted files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CommCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Compare" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CommCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show usage information


def test_execute_single_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CommCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd"])
    assert result == 1
    # Should require two files


def test_execute_nonexistent_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CommCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent1", "/nonexistent2"])
    # Should fail for nonexistent files
    assert result == 1
