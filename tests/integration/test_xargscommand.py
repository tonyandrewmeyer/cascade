"""Integration tests for the XargsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an XargsCommand instance."""
    yield pebble_shell.commands.XargsCommand(shell=shell)


def test_name(command: pebble_shell.commands.XargsCommand):
    assert command.name == "xargs"


def test_category(command: pebble_shell.commands.XargsCommand):
    assert command.category == "Advanced Utilities"


def test_help(command: pebble_shell.commands.XargsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "execute" in capture.get() or "arguments" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "xargs" in capture.get() or "execute" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    # xargs without arguments should succeed using default command
    assert result == 0


def test_execute_with_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["echo"])
    # Should succeed executing echo command
    assert result == 0


def test_execute_with_max_args_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-n", "2", "echo"])
    # Should succeed executing echo command
    assert result == 0


def test_execute_with_delimiter_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-d", "\n", "echo"])
    # Should succeed executing echo command
    assert result == 0


def test_execute_with_null_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-0", "echo"])
    # Should succeed executing echo command
    assert result == 0


def test_execute_with_interactive_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-p", "echo"])
    # Should succeed executing echo command
    assert result == 0


def test_execute_with_complex_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.XargsCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-n", "1", "ls", "-la"])
    # Should succeed executing echo command
    assert result == 0
