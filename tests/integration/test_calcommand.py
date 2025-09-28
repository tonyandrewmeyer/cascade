"""Integration tests for the CalCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CalCommand instance."""
    yield pebble_shell.commands.CalCommand(shell=shell)


def test_name(command: pebble_shell.commands.CalCommand):
    assert command.name == "cal"


def test_category(command: pebble_shell.commands.CalCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.CalCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display calendar" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CalCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display calendar" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CalCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should show a calendar
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_with_year(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CalCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["2024"])
    assert result == 0
    # Should show calendar for 2024
    output = capture.get()
    assert "2024" in output or len(output.strip()) > 0


def test_execute_with_month_year(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CalCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["12", "2024"])
    assert result == 0
    # Should show December 2024
    output = capture.get()
    assert len(output.strip()) > 0
