"""Integration tests for the LoadavgCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LoadavgCommand instance."""
    yield pebble_shell.commands.LoadavgCommand(shell=shell)


def test_name(command: pebble_shell.commands.LoadavgCommand):
    assert command.name == "loadavg"


def test_category(command: pebble_shell.commands.LoadavgCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.LoadavgCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "load average" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoadavgCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "load average" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoadavgCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should show load average information
    output = capture.get()
    assert len(output.strip()) > 0
