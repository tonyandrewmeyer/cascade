"""Integration tests for the UnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a UnameCommand instance."""
    yield pebble_shell.commands.UnameCommand(shell=shell)


def test_name(command: pebble_shell.commands.UnameCommand):
    assert command.name == "uname"


def test_category(command: pebble_shell.commands.UnameCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.UnameCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "system information" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "system information" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should print something (system name)
    assert len(capture.get().strip()) > 0


def test_execute_all_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])
    assert result == 0
    # Should print detailed system information
    assert len(capture.get().strip()) > 0


def test_execute_kernel_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])
    assert result == 0
    # Should print kernel name
    assert len(capture.get().strip()) > 0


def test_execute_kernel_release(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r"])
    assert result == 0
    # Should print kernel release
    assert len(capture.get().strip()) > 0


def test_execute_machine(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnameCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])
    assert result == 0
    # Should print machine hardware
    assert len(capture.get().strip()) > 0
