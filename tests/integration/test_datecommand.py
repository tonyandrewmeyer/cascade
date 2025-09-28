"""Integration tests for the DateCommand."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DateCommand instance."""
    yield pebble_shell.commands.DateCommand(shell=shell)


def test_name(command: pebble_shell.commands.DateCommand):
    assert command.name == "date"


def test_category(command: pebble_shell.commands.DateCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.DateCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show the current date and time" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DateCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show the current date and time" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DateCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Expected output is like:
    # Sat Jul 26 12:57:42  2025
    output_time = datetime.datetime.strptime(
        capture.get().strip(), "%a %b %d %H:%M:%S %Y"
    )
    assert (datetime.datetime.now() - output_time) < datetime.timedelta(seconds=5)


def test_execute_with_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DateCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["+%Y"])
    assert result == 0
    output_year = int(capture.get().strip())
    current_year = datetime.datetime.now().year
    assert output_year == current_year, f"Expected {current_year}, got {output_year}"


def test_execute_with_invalid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DateCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["+%invalid"])
    assert result == 1
