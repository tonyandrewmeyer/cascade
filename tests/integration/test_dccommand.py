"""Integration tests for the DcCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DcCommand instance."""
    yield pebble_shell.commands.DcCommand(shell=shell)


def test_name(command: pebble_shell.commands.DcCommand):
    assert command.name == "dc"


def test_category(command: pebble_shell.commands.DcCommand):
    assert command.category == "Mathematical Utilities"


def test_help(command: pebble_shell.commands.DcCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "calculator" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DcCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "calculator" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DcCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should succeed entering interactive mode
    assert result == 0


def test_execute_with_expression(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DcCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-e", "2 3 + p"])
    # Should calculate 2 + 3 = 5
    assert result == 0
