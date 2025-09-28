"""Integration tests for the ThemeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ThemeCommand instance."""
    yield pebble_shell.commands.ThemeCommand(shell=shell)


def test_name(command: pebble_shell.commands.ThemeCommand):
    assert command.name == "theme"


def test_category(command: pebble_shell.commands.ThemeCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.ThemeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Manage display themes" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Manage display themes" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    assert "Usage: theme" in capture.get()


def test_execute_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["list"])
    assert result == 0
    output = capture.get()
    assert "Available themes:" in output
    assert "default" in output


def test_execute_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])
    assert result == 0
    output = capture.get()
    assert "Current theme:" in output


def test_execute_set_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "default"])
    assert result == 0
    output = capture.get()
    assert "Theme set to: default" in output


def test_execute_set_invalid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "nonexistent"])
    assert result == 1
    output = capture.get()
    assert "Unknown theme" in output


def test_execute_invalid_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ThemeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid"])
    assert result == 1
    output = capture.get()
    assert "Unknown subcommand" in output
