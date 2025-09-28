"""Integration tests for the CatCommand."""

from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CatCommand instance."""
    yield pebble_shell.commands.CatCommand(shell=shell)


def test_name(command: pebble_shell.commands.CatCommand):
    assert command.name == "cat"


def test_category(command: pebble_shell.commands.CatCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.CatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display file contents" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display file contents" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: cat <file>" in capture.get()


def test_execute_temp_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, World!")
        temp_file_path = temp_file.name
    try:
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[temp_file_path])
        assert result == 0
        assert "Hello, World!" in capture.get()
    finally:
        os.remove(temp_file_path)


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    assert result == 1
