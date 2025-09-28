"""Integration tests for the GzipCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a GzipCommand instance."""
    yield pebble_shell.commands.GzipCommand(shell=shell)


def test_name(command: pebble_shell.commands.GzipCommand):
    assert command.name == "gzip"


def test_category(command: pebble_shell.commands.GzipCommand):
    assert command.category == "Compression"


def test_help(command: pebble_shell.commands.GzipCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compress or decompress files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GzipCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "gzip" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GzipCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show usage information
    output = capture.get()
    assert "Usage" in output or "usage" in output


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GzipCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    # Should fail for nonexistent file
    assert result == 1
