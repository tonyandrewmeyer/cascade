"""Integration tests for the LocalCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LocalCommand instance."""
    yield pebble_shell.commands.LocalCommand(shell=shell)


def test_name(command: pebble_shell.commands.LocalCommand):
    assert command.name == "local"


def test_category(command: pebble_shell.commands.LocalCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.LocalCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Run a local command" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LocalCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Run a local command" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LocalCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: local <subcommand>" in capture.get()


def test_execute_basic_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LocalCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["echo", "test"])
    assert result == 0
    assert "test" in capture.get()
