"""Integration tests for the SleepCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SleepCommand instance."""
    yield pebble_shell.commands.SleepCommand(shell=shell)


def test_name(command: pebble_shell.commands.SleepCommand):
    assert command.name == "sleep"


def test_category(command: pebble_shell.commands.SleepCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.SleepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Pause for a given number of seconds" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SleepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Pause for a given number of seconds" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SleepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: sleep SECONDS" in capture.get()


def test_execute_valid_sleep(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SleepCommand,
):
    start = time.time()
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["0.1"])
    assert result == 0
    assert time.time() - start >= 0.1


def test_execute_negative_sleep(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SleepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1"])
    assert result == 1
    assert "sleep: time may not be negative" in capture.get()


def test_execute_invalid_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SleepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid"])
    assert result == 1
    assert "invalid time interval 'invalid'" in capture.get()
