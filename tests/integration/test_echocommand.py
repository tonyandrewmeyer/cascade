"""Integration tests for the EchoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create an EchoCommand instance."""
    yield pebble_shell.commands.EchoCommand(shell=shell)


def test_name(command: pebble_shell.commands.EchoCommand):
    assert command.name == "echo"


def test_category(command: pebble_shell.commands.EchoCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.EchoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Display text" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Display text" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    assert result == 0
    assert capture.get() == "\n"


def test_execute_single_word(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["hello"])
    assert result == 0
    assert capture.get() == "hello\n"


def test_execute_multiple_words(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["hello", "world", "test"])
    assert result == 0
    assert capture.get() == "hello world test\n"


def test_flag_n_suppresses_newline(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "hello"])
    assert result == 0
    assert capture.get() == "hello"


def test_flag_e_processes_escapes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "hello\\nworld"])
    assert result == 0
    assert capture.get() == "hello\nworld\n"


def test_flag_upper_e_disables_escapes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-E", "hello\\nworld"])
    assert result == 0
    assert capture.get() == "hello\\nworld\n"


def test_escape_c_stops_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["hello\\cworld"])
    assert result == 0
    assert capture.get() == "hello"


def test_escape_octal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["\\0101"])
    assert result == 0
    assert capture.get() == "A\n"


def test_escape_hex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["\\x41"])
    assert result == 0
    assert capture.get() == "A\n"


def test_default_escapes_enabled(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    """Test that escape sequences are processed by default (BusyBox behavior)."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a\\tb"])
    assert result == 0
    output = capture.get()
    # Rich expands tabs in captured output, so check that 'a' and 'b'
    # are separated by whitespace (the expanded tab)
    assert output.startswith("a") and "b" in output
    assert output.strip() != "a\\tb"  # escapes were processed, not literal


def test_exit_code_always_zero(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    """Test that echo always returns exit code 0."""
    assert command.execute(client=client, args=[]) == 0
    assert command.execute(client=client, args=["hello"]) == 0
    assert command.execute(client=client, args=["-n", "test"]) == 0
    assert command.execute(client=client, args=["-E", "test"]) == 0


def test_multiple_args_joined_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EchoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a", "b", "c"])
    assert result == 0
    assert capture.get() == "a b c\n"
