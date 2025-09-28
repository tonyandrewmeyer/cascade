"""Integration tests for the StopCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a StopCommand instance."""
    yield pebble_shell.commands.StopCommand(shell=shell)


def test_name(command: pebble_shell.commands.StopCommand):
    assert command.name == "pebble-stop"


def test_category(command: pebble_shell.commands.StopCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.StopCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Stop one or more services" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Stop one or more services" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: stop <service-name>" in capture.get()


def test_execute_nonexistent_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["nonexistent-service"])
    assert result == 1
