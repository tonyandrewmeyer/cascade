"""Integration tests for the WhoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WhoCommand instance."""
    yield pebble_shell.commands.WhoCommand(shell=shell)


def test_name(command: pebble_shell.commands.WhoCommand):
    assert command.name == "who"


def test_category(command: pebble_shell.commands.WhoCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.WhoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "logged in users" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "logged in users" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhoCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # Should fail since no /var/run/utmp available in container
    assert result == 1
