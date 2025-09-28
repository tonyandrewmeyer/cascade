"""Integration tests for the AliasCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an AliasCommand instance."""
    yield pebble_shell.commands.AliasCommand(shell=shell)


def test_name(command: pebble_shell.commands.AliasCommand):
    assert command.name == "alias [name] [name=command]"


def test_category(command: pebble_shell.commands.AliasCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.AliasCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Manage command aliases" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Manage command aliases" in capture.get()


@pytest.mark.parametrize(
    "aliases",
    [
        {},
        {"ll": "ls -alh"},
        {"h": "history"},
        {
            "ll": "ls -l -a -h",
            "la": "ls -a",
            "l": "ls",
            "h": "history",
            "c": "clear",
            "q": "exit",
            "?": "help",
        },
    ],
)
def test_execute_show_all_aliases(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
    aliases: dict[str, str],
):
    command.aliases.clear()
    command.aliases.update(aliases)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    if not aliases:
        assert "No aliases defined" in capture.get()
        return
    for alias, definition in aliases.items():
        assert f"{alias} {definition}" in re.sub(r"\s+", " ", capture.get())


def test_execute_show_specific_alias(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ll"])
    assert result == 0
    assert "ll = ls -l -a -h" in capture.get()


def test_execute_show_nonexistent_alias(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent"])
    assert result == 1
    assert "not found" in capture.get()


def test_execute_set_alias(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test=echo hello"])
    assert result == 0
    assert "added" in capture.get()


def test_execute_invalid_alias_definition(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["invalid_without_equals"])
    assert result == 1


def test_execute_empty_alias_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AliasCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["=command"])
    assert result == 1
    assert "invalid alias name" in capture.get()


def test_get_alias(command: pebble_shell.commands.AliasCommand):
    # Test built-in aliases
    assert command.get_alias("ll") == "ls -l -a -h"
    assert command.get_alias("nonexistent") is None


def test_expand_alias(command: pebble_shell.commands.AliasCommand):
    # Test alias expansion
    assert command.expand_alias("ll") == "ls -l -a -h "
    assert command.expand_alias("ll -t") == "ls -l -a -h -t"
    assert command.expand_alias("unknown command") == "unknown command"
    assert command.expand_alias("") == ""
