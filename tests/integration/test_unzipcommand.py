"""Integration tests for the UnzipCommand."""

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
    """Fixture to create an UnzipCommand instance."""
    yield pebble_shell.commands.UnzipCommand(shell=shell)


def test_name(command: pebble_shell.commands.UnzipCommand):
    assert command.name == "unzip"


def test_category(command: pebble_shell.commands.UnzipCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.UnzipCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "extract files from ZIP" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "unzip" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show error message about missing file operand


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.zip"])
    # Should fail for nonexistent file
    assert result == 1


def test_execute_with_list_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-l", "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1


def test_execute_with_test_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-t", "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1


def test_execute_with_quiet_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-q", "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1


def test_execute_with_overwrite_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-o", "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1


def test_execute_with_directory_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-d", temp_dir, "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1


def test_execute_with_combined_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-qo", "/etc/passwd"])
    # Should fail since /etc/passwd is not a ZIP file
    assert result == 1
