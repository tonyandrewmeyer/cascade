"""Integration tests for the PrintenvCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PrintenvCommand instance."""
    yield pebble_shell.commands.PrintenvCommand(shell=shell)


def test_name(command: pebble_shell.commands.PrintenvCommand):
    assert command.name == "printenv"


def test_category(command: pebble_shell.commands.PrintenvCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.PrintenvCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Print environment variables" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintenvCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Print environment variables" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintenvCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should print environment variables (at least PATH should be present)
    output = capture.get()
    assert "PATH" in output or "=" in output  # Environment vars have = signs


def test_execute_specific_var(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintenvCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["PATH"])
    # Should succeed since PATH environment variable exists
    assert result == 0


def test_execute_nonexistent_var(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintenvCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["NONEXISTENT_VAR_123"])
    # Should return 1 for nonexistent variable
    assert result == 1
