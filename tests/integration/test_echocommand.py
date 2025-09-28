"""Integration tests for the EchoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an EchoCommand instance."""
    yield pebble_shell.commands.EchoCommand(shell=shell)


def test_name(command: pebble_shell.commands.EchoCommand):
    assert command.name == "echo"


def test_category(command: pebble_shell.commands.EchoCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.EchoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display text" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display text" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    assert capture.get().strip() == ""


def test_execute_single_word(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["hello"])
    assert result == 0
    assert "hello" in capture.get()


def test_execute_multiple_words(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["hello", "world", "test"])
    assert result == 0
    output = capture.get()
    assert "hello" in output
    assert "world" in output
    assert "test" in output
