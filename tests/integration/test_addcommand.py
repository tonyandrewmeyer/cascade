"""Integration tests for the AddCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pathlib

    import ops

import pytest

import pebble_shell.commands
import pebble_shell.shell


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an AddCommand instance."""
    yield pebble_shell.commands.AddCommand(shell=shell)


def test_name(command: pebble_shell.commands.AddCommand):
    assert command.name == "pebble-add"


def test_category(command: pebble_shell.commands.AddCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.AddCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Add a layer to the plan" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Add a layer to the plan" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 1
    assert "Usage: add <layer-name>" in capture.get()


def test_execute_with_temp_layer_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddCommand,
    tmp_path: pathlib.Path,
):
    layer_file = tmp_path / "test_layer.yaml"
    layer_file.write_text("services:\n  test:\n    command: echo hello\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["test-layer", str(layer_file)])
    assert result == 0  # Should succeed adding a valid layer file
