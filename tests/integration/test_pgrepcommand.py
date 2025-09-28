"""Integration tests for the PgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PgrepCommand instance."""
    yield pebble_shell.commands.PgrepCommand(shell=shell)


def test_name(command: pebble_shell.commands.PgrepCommand):
    assert command.name == "pgrep [-f] [-u user] [pattern]"


def test_category(command: pebble_shell.commands.PgrepCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.PgrepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Find processes" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Find processes" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    # Should show usage information
    assert "Usage:" in capture.get()


def test_execute_with_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["init"])
    # Should fail since 'init' process likely doesn't exist in container
    assert result == 1


def test_execute_with_full_match_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-f", "system"])
    # Should fail since 'system' process likely doesn't exist
    assert result == 1


def test_execute_with_user_filter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-u", "root", "init"])
    # Should fail since 'init' process under root likely doesn't exist
    assert result == 1


def test_execute_user_filter_no_username(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-u"])
    assert result == 1
    # Should show error message
    assert "requires a username" in capture.get()


def test_execute_unknown_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x"])
    assert result == 1
    # Should show error for unknown option
    assert "Unknown option" in capture.get()


def test_execute_user_only_no_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PgrepCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-u", "root"])
    # Should succeed listing processes for root user
    assert result == 0
