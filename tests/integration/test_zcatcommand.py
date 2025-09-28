"""Integration tests for the ZcatCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ZcatCommand instance."""
    yield pebble_shell.commands.ZcatCommand(shell=shell)


def test_name(command: pebble_shell.commands.ZcatCommand):
    assert command.name == "zcat"


def test_category(command: pebble_shell.commands.ZcatCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.ZcatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Decompress and print .gz files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ZcatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Decompress and print .gz files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ZcatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Check for usage message in output
    output = capture.get()
    assert "Usage:" in output and "zcat" in output


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ZcatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.gz"])
    # Should return error code for nonexistent file
    assert result == 1
    # Should print an error message
    assert "zcat:" in capture.get()
