"""Integration tests for the PrintfCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PrintfCommand instance."""
    yield pebble_shell.commands.PrintfCommand(shell=shell)


def test_name(command: pebble_shell.commands.PrintfCommand):
    assert command.name == "printf"


def test_category(command: pebble_shell.commands.PrintfCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.PrintfCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "Format and print data" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "Format and print data" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    # Should fail with missing format string error
    assert result == 1
    assert "missing format string" in capture.get()


def test_execute_simple_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello World"])
    # Should succeed and print the string
    assert result == 0
    assert capture.get() == "Hello World"


def test_execute_string_with_newline(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello\\nWorld"])
    # Should succeed and process newline escape
    assert result == 0
    assert capture.get() == "Hello\nWorld"


def test_execute_string_with_tab(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello\\tWorld"])
    # Should succeed and process tab escape
    assert result == 0
    assert capture.get() == "Hello\tWorld"


def test_execute_string_with_backslash(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello\\\\World"])
    # Should succeed and process backslash escape
    assert result == 0
    assert capture.get() == "Hello\\World"


def test_execute_string_substitution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello %s", "World"])
    # Should succeed and substitute string
    assert result == 0
    assert capture.get() == "Hello World"


def test_execute_decimal_integer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Number: %d", "42"])
    # Should succeed and format decimal integer
    assert result == 0
    assert capture.get() == "Number: 42"


def test_execute_decimal_integer_invalid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Number: %d", "invalid"])
    # Should succeed but use default value 0 for invalid input
    assert result == 0
    assert capture.get() == "Number: 0"


def test_execute_octal_integer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Octal: %o", "8"])
    # Should succeed and format as octal
    assert result == 0
    assert capture.get() == "Octal: 10"


def test_execute_hex_lowercase(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hex: %x", "255"])
    # Should succeed and format as lowercase hex
    assert result == 0
    assert capture.get() == "Hex: ff"


def test_execute_hex_uppercase(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hex: %X", "255"])
    # Should succeed and format as uppercase hex
    assert result == 0
    assert capture.get() == "Hex: FF"


def test_execute_floating_point(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Float: %f", "3.14"])
    # Should succeed and format floating point
    assert result == 0
    assert capture.get() == "Float: 3.14"


def test_execute_floating_point_invalid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Float: %f", "invalid"])
    # Should succeed but use default value 0.0 for invalid input
    assert result == 0
    assert capture.get() == "Float: 0.0"


def test_execute_character(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Char: %c", "Hello"])
    # Should succeed and use first character
    assert result == 0
    assert capture.get() == "Char: H"


def test_execute_literal_percent(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Percent: %%"])
    # Should succeed and print literal percent
    assert result == 0
    assert capture.get() == "Percent: %"


def test_execute_multiple_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%d + %d = %d", "2", "3", "5"])
    # Should succeed and substitute all arguments
    assert result == 0
    assert capture.get() == "2 + 3 = 5"


def test_execute_insufficient_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%s %d %f", "hello"])
    # Should succeed but use defaults for missing arguments
    assert result == 0
    assert capture.get() == "hello 0 0.0"


def test_execute_excess_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%s", "hello", "world", "extra"])
    # Should succeed and ignore extra arguments
    assert result == 0
    assert capture.get() == "hello"


def test_execute_unknown_specifier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Test: %z", "value"])
    # Should succeed and handle unknown specifier literally
    assert result == 0
    assert capture.get() == "Test: %z"


def test_execute_complex_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "User: %s, ID: %d, Hex: 0x%x, Float: %f%%\\n",
                "alice",
                "1001",
                "16",
                "98.6",
            ],
        )
    # Should succeed with complex formatting
    assert result == 0
    assert capture.get() == "User: alice, ID: 1001, Hex: 0x10, Float: 98.6%\n"


def test_execute_empty_format_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])
    # Should succeed with empty format string
    assert result == 0
    assert capture.get() == ""


def test_execute_only_escape_sequences(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["\\n\\t\\\\"])
    # Should succeed and process all escape sequences
    assert result == 0
    assert capture.get() == "\n\t\\"


def test_execute_character_empty_arg(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Char: %c", ""])
    # Should succeed but print nothing for empty character argument
    assert result == 0
    assert capture.get() == "Char: "


def test_execute_i_specifier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PrintfCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Integer: %i", "42"])
    # Should succeed and format with %i (same as %d)
    assert result == 0
    assert capture.get() == "Integer: 42"
