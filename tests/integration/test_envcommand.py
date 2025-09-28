"""Integration tests for the EnvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an EnvCommand instance."""
    yield pebble_shell.commands.EnvCommand(shell=shell)


def test_name(command: pebble_shell.commands.EnvCommand):
    assert command.name == "env"


def test_category(command: pebble_shell.commands.EnvCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.EnvCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show environment variables" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show environment variables" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Result can be 0 or 1 depending on whether env files exist
    assert result == 0
