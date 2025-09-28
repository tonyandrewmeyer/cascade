"""Integration tests for the CutCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CutCommand instance."""
    yield pebble_shell.commands.CutCommand(shell=shell)


def test_name(command: pebble_shell.commands.CutCommand):
    assert (
        command.name
        == "cut [-f fields] [-d delimiter] [-c characters] <file> [file2...]"
    )


def test_category(command: pebble_shell.commands.CutCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.CutCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Extract fields or characters from files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Extract fields or characters from files" in capture.get()


def test_execute_insufficient_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file"])
    assert result == 1
    assert "Usage: cut -f fields" in capture.get()


def test_execute_missing_f_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f"])
    assert result == 1
    assert "Error: Flag -f requires an argument" in capture.get()


def test_execute_missing_c_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])
    assert result == 1
    assert "Error: Flag -c requires an argument" in capture.get()


def test_execute_missing_d_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d"])
    assert result == 1
    assert "Error: Flag -d requires an argument" in capture.get()


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "file"])
    assert result == 1
    assert "Error: Invalid option -x" in capture.get()


def test_execute_no_input_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "1"])
    assert result == 1
    assert "Usage: cut [-f|-c] <file>" in capture.get()


def test_execute_no_fields_or_chars(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CutCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file"])
    assert result == 1
    assert "cut: you must specify -f (fields) or -c (characters)" in capture.get()
