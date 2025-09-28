"""Integration tests for the UptimeCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an UptimeCommand instance."""
    yield pebble_shell.commands.UptimeCommand(shell=shell)


def test_name(command: pebble_shell.commands.UptimeCommand):
    assert command.name == "uptime"


def test_category(command: pebble_shell.commands.UptimeCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.UptimeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show system uptime and load" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UptimeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show system uptime and load" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UptimeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # The output will look something like:
    # 12:40:53 up 22 hours, 44 minutes, load average: 1.02, 1.23, 1.22
    output = capture.get()
    mo = re.match(
        r"^\d{2}:\d{2}:\d{2} up \d+ hours?, \d+ minutes?, load average: [\d.]+, [\d.]+, [\d.]+$",
        output.strip(),
    )
    assert mo is not None


def test_execute_with_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UptimeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p"])
    assert result == 1
    assert "Usage: uptime" in capture.get()
