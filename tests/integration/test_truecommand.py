"""Integration tests for the TrueCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TrueCommand instance."""
    yield pebble_shell.commands.TrueCommand(shell=shell)


def test_name(command: pebble_shell.commands.TrueCommand):
    assert command.name == "true"


def test_category(command: pebble_shell.commands.TrueCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.TrueCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Return a successful exit code (0)" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TrueCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Return a successful exit code (0)" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TrueCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TrueCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["any", "args", "ignored"])
    assert result == 0
