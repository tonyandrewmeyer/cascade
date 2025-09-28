"""Integration tests for the EditCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an EditCommand instance."""
    yield pebble_shell.commands.EditCommand(shell=shell)


def test_name(command: pebble_shell.commands.EditCommand):
    assert command.name == "edit"


def test_category(command: pebble_shell.commands.EditCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.EditCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Edit a remote file locally" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EditCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Edit a remote file locally" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EditCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "No remote file specified" in capture.get()


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EditCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])
    # Should fail for nonexistent file
    assert result == 1
