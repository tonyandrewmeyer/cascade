"""Integration tests for the StatCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a StatCommand instance."""
    yield pebble_shell.commands.StatCommand(shell=shell)


def test_name(command: pebble_shell.commands.StatCommand):
    assert command.name == "stat"


def test_category(command: pebble_shell.commands.StatCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.StatCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show file/directory statistics" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StatCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show file/directory statistics" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    output = capture.get()
    # Should indicate usage or requirement error
    assert any(phrase in output for phrase in ["Usage:", "requires", "expected"])


def test_execute_root_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StatCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])
    output = capture.get()
    # Should succeed since root directory exists
    assert result == 0
    # Should have stat information for root directory
    assert any(keyword in output for keyword in ["Size:", "Access:", "File:", "Type:"])


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StatCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file"])
    assert result == 1
