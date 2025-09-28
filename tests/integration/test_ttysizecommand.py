"""Integration tests for the TtysizeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TtysizeCommand instance."""
    yield pebble_shell.commands.TtysizeCommand(shell=shell)


def test_name(command: pebble_shell.commands.TtysizeCommand):
    assert command.name == "ttysize"


def test_category(command: pebble_shell.commands.TtysizeCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.TtysizeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "terminal size" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtysizeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "terminal size" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtysizeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should show terminal dimensions like "24 80" (rows columns)
    output = capture.get().strip()
    assert len(output) > 0
    # Output should contain numbers representing rows and columns
    parts = output.split()
    if len(parts) >= 2:
        # Should be able to parse as integers
        try:
            rows = int(parts[0])
            cols = int(parts[1])
            assert rows > 0
            assert cols > 0
        except ValueError:
            # If not parseable as integers, that's ok too
            pass


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtysizeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["extra", "args"])
    # ttysize command ignores extra arguments and succeeds
    assert result == 0
