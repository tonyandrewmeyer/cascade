"""Integration tests for the SeqCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SeqCommand instance."""
    yield pebble_shell.commands.SeqCommand(shell=shell)


def test_name(command: pebble_shell.commands.SeqCommand):
    assert command.name == "seq"


def test_category(command: pebble_shell.commands.SeqCommand):
    assert command.category == "Text Utilities"


def test_help(command: pebble_shell.commands.SeqCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Generate sequences" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SeqCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Generate sequences" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SeqCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show usage information


def test_execute_single_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SeqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["5"])
    assert result == 0
    # Should generate sequence 1 to 5
    output = capture.get()
    assert "1" in output and "5" in output


def test_execute_range(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SeqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["3", "7"])
    assert result == 0
    # Should generate sequence 3 to 7
    output = capture.get()
    assert "3" in output and "7" in output


def test_execute_invalid_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SeqCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["invalid"])
    assert result == 1
