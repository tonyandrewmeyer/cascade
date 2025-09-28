"""Integration tests for the FindCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FindCommand instance."""
    yield pebble_shell.commands.FindCommand(shell=shell)


def test_name(command: pebble_shell.commands.FindCommand):
    assert command.name == "find"


def test_category(command: pebble_shell.commands.FindCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.FindCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Find files matching pattern" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Find files matching pattern" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: find <search_path>" in capture.get()


def test_execute_find_root(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc", "*"])
    assert result == 0


def test_execute_find_by_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FindCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc", "passwd"])
    assert result == 0  # Should succeed since passwd file exists in /etc
