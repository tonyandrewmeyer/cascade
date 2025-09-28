"""Integration tests for the LzmaCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LzmaCommand instance."""
    yield pebble_shell.commands.LzmaCommand(shell=shell)


def test_name(command: pebble_shell.commands.LzmaCommand):
    assert command.name == "lzma"


def test_category(command: pebble_shell.commands.LzmaCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.LzmaCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compress or decompress files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "lzma" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show error message about missing file operand


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    # Should fail for nonexistent file
    assert result == 1


def test_execute_with_decompress_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-d", "/etc/passwd"])
    # Should fail since /etc/passwd is not an LZMA file
    assert result == 1


def test_execute_with_keep_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-k", "/etc/passwd"])
    # Should fail since /etc/passwd is not compressed
    assert result == 1


def test_execute_with_force_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-f", "/etc/passwd"])
    # Should fail since /etc/passwd is not compressed
    assert result == 1


def test_execute_with_verbose_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-v", "/etc/passwd"])
    # Should fail since /etc/passwd is not compressed
    assert result == 1


def test_execute_with_combined_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LzmaCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-kv", "/etc/passwd"])
    # Should fail since /etc/passwd is not compressed
    assert result == 1
