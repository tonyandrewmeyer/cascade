"""Integration tests for the YesCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a YesCommand instance."""
    yield pebble_shell.commands.YesCommand(shell=shell)


def test_name(command: pebble_shell.commands.YesCommand):
    assert command.name == "yes"


def test_category(command: pebble_shell.commands.YesCommand):
    assert command.category == "Advanced Utilities"


def test_help(command: pebble_shell.commands.YesCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "repeatedly output" in capture.get() or "print" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YesCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "yes" in capture.get() or "output" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YesCommand,
):
    # Note: yes command normally runs infinitely, so it may time out
    # The implementation should handle this appropriately
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should succeed printing 'y' repeatedly
    assert result == 0


def test_execute_with_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YesCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["hello"])
    # Should succeed printing 'hello' repeatedly
    assert result == 0


def test_execute_with_multiple_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YesCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["hello", "world"])
    # Should succeed printing 'hello world' repeatedly
    assert result == 0
