"""Integration tests for the TailCommand."""

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
    """Fixture to create a TailCommand instance."""
    yield pebble_shell.commands.TailCommand(shell=shell)


def test_name(command: pebble_shell.commands.TailCommand):
    assert command.name == "tail"


def test_category(command: pebble_shell.commands.TailCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.TailCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display last lines of file" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TailCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display last lines of file" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TailCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    assert "Usage: tail" in output and "file" in output and "[-f]" in output


def test_execute_with_temp_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TailCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Test line 1\nTest line 2\nTest line 3\n")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[temp_file_path])
        assert result == 0
        assert "Test line 1" in capture.get()
        assert "Test line 2" in capture.get()
        assert "Test line 3" in capture.get()
    finally:
        os.remove(temp_file_path)


def test_execute_with_lines_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TailCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["-n", "3", temp_file_path])
        assert result == 0
        output = capture.get()
        assert "Line 3" in output
        assert "Line 4" in output
        assert "Line 5" in output
        assert "Line 1" not in output
        assert "Line 2" not in output
    finally:
        os.remove(temp_file_path)
