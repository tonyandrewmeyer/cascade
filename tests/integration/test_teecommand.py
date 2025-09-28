"""Integration tests for the TeeCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TeeCommand instance."""
    yield pebble_shell.commands.TeeCommand(shell=shell)


def test_name(command: pebble_shell.commands.TeeCommand):
    assert command.name == "tee"


def test_category(command: pebble_shell.commands.TeeCommand):
    assert command.category == "Advanced Utilities"


def test_help(command: pebble_shell.commands.TeeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "copy" in capture.get() or "write" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "tee" in capture.get() or "copy" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # tee without files should succeed (read from stdin, write to stdout)
    assert result == 0


def test_execute_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with tempfile.NamedTemporaryFile(suffix="_test_tee.txt", delete=False) as temp_file:
        temp_path = temp_file.name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[temp_path])
    # Should succeed writing to temporary file
    assert result == 0


def test_execute_with_append_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with tempfile.NamedTemporaryFile(suffix="_test_tee.txt", delete=False) as temp_file:
        temp_path = temp_file.name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-a", temp_path])
    # Should succeed with append flag to temporary file
    assert result == 0


def test_execute_with_ignore_interrupts_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with tempfile.NamedTemporaryFile(suffix="_test_tee.txt", delete=False) as temp_file:
        temp_path = temp_file.name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-i", temp_path])
    # Should succeed with ignore interrupts flag to temporary file
    assert result == 0


def test_execute_with_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with tempfile.NamedTemporaryFile(suffix="_file1.txt", delete=False) as temp_file1:
        temp_path1 = temp_file1.name
    with tempfile.NamedTemporaryFile(suffix="_file2.txt", delete=False) as temp_file2:
        temp_path2 = temp_file2.name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[temp_path1, temp_path2])
    # Should succeed writing to multiple temporary files
    assert result == 0


def test_execute_with_combined_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TeeCommand,
):
    with tempfile.NamedTemporaryFile(suffix="_test_tee.txt", delete=False) as temp_file:
        temp_path = temp_file.name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-ai", temp_path])
    # Should succeed with combined flags to temporary file
    assert result == 0
