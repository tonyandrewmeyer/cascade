"""Integration tests for the CdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CdCommand instance."""
    yield pebble_shell.commands.CdCommand(shell=shell)


def test_name(command: pebble_shell.commands.CdCommand):
    assert command.name == "cd"


def test_category(command: pebble_shell.commands.CdCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.CdCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Change directory" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Change directory" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CdCommand,
):
    original_dir = command.shell.current_directory = "/"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should change to home directory
    assert command.shell.current_directory != original_dir


@pytest.mark.parametrize("directory", ["/", "/var", "/etc"])
def test_execute_valid_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CdCommand,
    directory: str,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[directory])
    assert result == 0  # Should succeed for standard directories


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CdCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/directory"])
    assert result == 1
