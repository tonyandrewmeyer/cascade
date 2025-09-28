"""Integration tests for the HistoryCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a HistoryCommand instance."""
    yield pebble_shell.commands.HistoryCommand(shell=shell)


def test_name(command: pebble_shell.commands.HistoryCommand):
    assert command.name == "history [-c] [-s] [count|pattern]"


def test_category(command: pebble_shell.commands.HistoryCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.HistoryCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show command history" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show command history" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_clear(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])
    assert result == 0
    assert "History cleared" in capture.get()


def test_execute_stats(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-s"])
    assert result == 0


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-x"])
    assert result == 0  # Shows usage help instead of error


def test_execute_with_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["10"])
    assert result == 0


def test_execute_with_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HistoryCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent_pattern"])
    # Returns 1 when no matches found
    assert result == 1
    assert "No history entries found" in capture.get()
