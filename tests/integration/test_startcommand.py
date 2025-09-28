"""Integration tests for the StartCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a StartCommand instance."""
    yield pebble_shell.commands.StartCommand(shell=shell)


def test_name(command: pebble_shell.commands.StartCommand):
    assert command.name == "pebble-start"


def test_category(command: pebble_shell.commands.StartCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.StartCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Start one or more services" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StartCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Start one or more services" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StartCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: start <service-name>" in capture.get()


def test_execute_nonexistent_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StartCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["nonexistent-service"])
    assert result == 1
