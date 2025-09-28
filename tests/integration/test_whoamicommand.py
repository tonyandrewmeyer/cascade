"""Integration tests for the WhoamiCommand."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WhoamiCommand instance."""
    yield pebble_shell.commands.WhoamiCommand(shell=shell)


def test_name(command: pebble_shell.commands.WhoamiCommand):
    assert command.name == "whoami"


def test_category(command: pebble_shell.commands.WhoamiCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.WhoamiCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show current user" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhoamiCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show current user" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WhoamiCommand,
):
    correct_username = subprocess.check_output(["whoami"], text=True).strip()  # noqa: S607
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Output currently looks like:
    # uid=1000(ubuntu)
    # TODO: Why does it look like that? It doesn't on macOS or Ubuntu in my testing.
    assert correct_username in capture.get()
