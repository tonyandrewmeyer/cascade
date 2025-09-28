"""Integration tests for the TacCommand."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TacCommand instance."""
    yield pebble_shell.commands.TacCommand(shell=shell)


def test_name(command: pebble_shell.commands.TacCommand):
    assert command.name == "tac"


def test_category(command: pebble_shell.commands.TacCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.TacCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Concatenate and print files in reverse" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TacCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Concatenate and print files in reverse" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TacCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    output = capture.get()
    assert result == 1
    assert "Usage: tac" in output


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TacCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    assert result == 1


def test_execute_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TacCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Line 1\nLine 2\nLine 3\n")
        temp_file_path = temp_file.name

    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[temp_file_path])
        output = capture.get()
        assert result == 0
        assert output.strip() == "Line 3\nLine 2\nLine 1"
    finally:
        os.remove(temp_file_path)
