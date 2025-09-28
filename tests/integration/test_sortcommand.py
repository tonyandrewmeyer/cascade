"""Integration tests for the SortCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SortCommand instance."""
    yield pebble_shell.commands.SortCommand(shell=shell)


def test_name(command: pebble_shell.commands.SortCommand):
    assert command.name == "sort [-r] [-n] [-k field] <file> [file2...]"


def test_category(command: pebble_shell.commands.SortCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.SortCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Sort lines in files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Sort lines in files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: sort [-r] [-n] [-k field] <file>" in capture.get()


def test_execute_invalid_field_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k", "invalid", "file"])
    assert result == 1
    assert "Error: Flag -k requires an integer argument" in capture.get()


def test_execute_missing_k_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k"])
    assert result == 1
    assert "Error: Flag -k requires an argument" in capture.get()


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "file"])
    assert result == 1
    assert "Error: Invalid option -x" in capture.get()


def test_execute_no_input_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SortCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r"])
    assert result == 1
    assert "Usage: sort [-r] [-n] [-k field] <file>" in capture.get()
