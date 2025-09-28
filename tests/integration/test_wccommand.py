"""Integration tests for the WcCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WcCommand instance."""
    yield pebble_shell.commands.WcCommand(shell=shell)


def test_name(command: pebble_shell.commands.WcCommand):
    assert command.name == "wc [-l|-w|-c] <file> [file2...]"


def test_category(command: pebble_shell.commands.WcCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.WcCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Count lines, words, and characters in files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WcCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Count lines, words, and characters in files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WcCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: wc [-l|-w|-c] <file>" in capture.get()


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WcCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "file"])
    assert result == 1
    assert "Error: Invalid option -x" in capture.get()


def test_execute_no_files_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WcCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])
    assert result == 1
    assert "Usage: wc [-l|-w|-c] <file>" in capture.get()
