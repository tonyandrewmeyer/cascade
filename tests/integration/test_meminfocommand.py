"""Integration tests for the MeminfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MeminfoCommand instance."""
    yield pebble_shell.commands.MeminfoCommand(shell=shell)


def test_name(command: pebble_shell.commands.MeminfoCommand):
    assert command.name == "meminfo [-d] [-s]"


def test_category(command: pebble_shell.commands.MeminfoCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.MeminfoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "memory information" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MeminfoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "memory information" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MeminfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should print memory information
    output = capture.get()
    assert len(output.strip()) > 0
    # Common memory fields that should be present
    assert any(
        field in output
        for field in ["MemTotal", "MemFree", "MemAvailable", "Buffers", "Cached"]
    )
