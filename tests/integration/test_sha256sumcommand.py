"""Integration tests for the Sha256sumCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a Sha256sumCommand instance."""
    yield pebble_shell.commands.Sha256sumCommand(shell=shell)


def test_name(command: pebble_shell.commands.Sha256sumCommand):
    assert command.name == "sha256sum"


def test_category(command: pebble_shell.commands.Sha256sumCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.Sha256sumCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Compute SHA256 hash of a file or stdin" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Sha256sumCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Compute SHA256 hash of a file or stdin" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Sha256sumCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: sha256sum <file>" in capture.get()


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Sha256sumCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    # Should fail because file doesn't exist
    assert result == 1
