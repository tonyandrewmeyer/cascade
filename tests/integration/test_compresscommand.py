"""Integration tests for the CompressCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CompressCommand instance."""
    yield pebble_shell.commands.CompressCommand(shell=shell)


def test_name(command: pebble_shell.commands.CompressCommand):
    assert command.name == "compress"


def test_category(command: pebble_shell.commands.CompressCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.CompressCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compress files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "compress" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show error message about missing file operand


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    # Should fail for nonexistent file
    assert result == 1


def test_execute_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd"])
    # Should fail since /etc/passwd cannot be compressed to same location
    assert result == 1


def test_execute_with_force_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-f", "/etc/passwd"])
    # Should fail since /etc/passwd cannot be compressed to same location
    assert result == 1


def test_execute_with_verbose_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-v", "/etc/passwd"])
    # Should fail since /etc/passwd cannot be compressed to same location
    assert result == 1


def test_execute_with_combined_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-fv", "/etc/passwd"])
    # Should fail since /etc/passwd cannot be compressed to same location
    assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CompressCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "/etc/hosts"])
    # Should fail since these files cannot be compressed to same location
    assert result == 1
