"""Integration tests for the TtyCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TtyCommand instance."""
    yield pebble_shell.commands.TtyCommand(shell=shell)


def test_name(command: pebble_shell.commands.TtyCommand):
    assert command.name == "tty"


def test_category(command: pebble_shell.commands.TtyCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.TtyCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "terminal" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtyCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "terminal" in capture.get()


def test_execute_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtyCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    # Should show terminal name or "not a tty"
    output = capture.get().strip()
    assert len(output) > 0
    # Common outputs include device names like /dev/pts/0 or "not a tty"
    assert output.startswith("/") or "not a tty" in output or "tty" in output


def test_execute_with_silent_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtyCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])
    # Silent mode should succeed without output
    assert result == 0
    # Should have no output in silent mode
    output = capture.get().strip()
    assert len(output) == 0


def test_execute_with_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TtyCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["extra", "args"])
    # tty command ignores extra arguments and succeeds
    assert result == 0
