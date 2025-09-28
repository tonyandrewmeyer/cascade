"""Integration tests for the TimeCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TimeCommand instance."""
    yield pebble_shell.commands.TimeCommand(shell=shell)


def test_name(command: pebble_shell.commands.TimeCommand):
    assert command.name == "time"


def test_category(command: pebble_shell.commands.TimeCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.TimeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Time the execution" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TimeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Time the execution" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TimeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "missing command" in capture.get()


def test_execute_with_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TimeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["true"])
    assert result == 0
    # The output should look like:
    # real0m02.069s
    mo = re.search(
        r"real\s+(\d+)m(\d+\.\d+)s",
        capture.get(),
    )
    assert mo is not None, "Output should contain timing information"
