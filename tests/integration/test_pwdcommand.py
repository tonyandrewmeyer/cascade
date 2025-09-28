"""Integration tests for the 'pwd' command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PwdCommand instance."""
    yield pebble_shell.commands.PwdCommand(shell=shell)


def test_name(command: pebble_shell.commands.PwdCommand):
    assert command.name == "pwd"


def test_category(command: pebble_shell.commands.PwdCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.PwdCommand):
    command.show_help()
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Print current directory" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PwdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Print current directory" in capture.get()


@pytest.mark.parametrize("current_dir", ["/home/ubuntu", "/var/log", "/var", "/"])
def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PwdCommand,
    current_dir: str,
):
    with command.shell.console.capture() as capture:
        command.shell.current_directory = current_dir
        result = command.execute(client=client, args=[])
    assert result == 0
    assert capture.get().strip() == current_dir


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PwdCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["extra_arg"])
    assert result == 1
    assert "Error: This command does not accept any arguments" in capture.get()
