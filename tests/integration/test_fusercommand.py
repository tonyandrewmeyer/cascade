"""Integration tests for the FuserCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FuserCommand instance."""
    yield pebble_shell.commands.FuserCommand(shell=shell)


def test_name(command: pebble_shell.commands.FuserCommand):
    assert command.name == "fuser"


def test_category(command: pebble_shell.commands.FuserCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.FuserCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Show processes using files" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FuserCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Show processes using files" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FuserCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "no files specified" in capture.get()


@pytest.mark.skip("The implementation is incredibly slow and needs work.")
def test_execute_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FuserCommand,
):
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[temp_dir])
    assert result == 0


@pytest.mark.skip("The implementation is incredibly slow and needs work.")
def test_execute_with_verbose_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FuserCommand,
):
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-v", temp_dir])
    assert result == 0


@pytest.mark.skip("The implementation is incredibly slow and needs work.")
def test_execute_with_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FuserCommand,
):
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[temp_dir, "/var"])
    assert result == 0
