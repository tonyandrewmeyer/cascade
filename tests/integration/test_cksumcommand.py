"""Integration tests for the CksumCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CksumCommand instance."""
    yield pebble_shell.commands.CksumCommand(shell=shell)


def test_name(command: pebble_shell.commands.CksumCommand):
    assert command.name == "cksum"


def test_category(command: pebble_shell.commands.CksumCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.CksumCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "CRC checksum" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CksumCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "checksum" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CksumCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should show usage since no file provided
    assert result == 1


def test_execute_existing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CksumCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd"])
    # Should succeed since /etc/passwd exists
    assert result == 0


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CksumCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    # Should fail for nonexistent file
    assert result == 1
