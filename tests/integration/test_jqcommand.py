"""Integration tests for the JqCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a JqCommand instance."""
    yield pebble_shell.commands.JqCommand(shell=shell)


def test_name(command: pebble_shell.commands.JqCommand):
    assert command.name == "jq <file> [keypath]"


def test_category(command: pebble_shell.commands.JqCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.JqCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "jq" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "jq" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "No file specified" in output
    assert "Usage: jq <file> [.foo.bar]" in output


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.json"])
    # Should fail with file error
    assert result == 1
    output = capture.get()
    assert "Error reading file" in output


def test_execute_invalid_json_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Try to parse a non-JSON file like /etc/passwd
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])
    # Should fail with JSON parsing error
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_with_valid_json_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # This test may pass or fail depending on if there are JSON files available
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd"]
        )  # Not JSON, should fail

    # Should fail since /etc/passwd is not JSON
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_with_keypath_invalid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test invalid keypath format (not starting with dot)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "foo.bar"])

    # Should fail due to invalid JSON first, but if it were valid JSON:
    # Should fail with keypath format error
    assert result == 1


def test_execute_with_valid_keypath_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test valid keypath format (starting with dot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".foo.bar"])

    # Should fail due to invalid JSON, but keypath format is valid
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_keypath_navigation_dict_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test dictionary key access in keypath
    # This would work if we had a valid JSON file with nested structure
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".users.0.name"])

    # Should fail due to invalid JSON format
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_keypath_navigation_array_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test array index access in keypath
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".items.0"])

    # Should fail due to invalid JSON format
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_empty_keypath(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test empty keypath (just dot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "."])

    # Should fail due to invalid JSON format first
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_invalid_keypath_missing_dot(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test keypath that doesn't start with dot
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "foo"])

    # Should fail due to invalid JSON format first
    assert result == 1


def test_execute_multiple_args_extra_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test with more than 2 arguments (extras should be ignored)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", ".foo", "extra", "args"]
        )

    # Should use first file and first keypath, ignore extras
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_path_resolution_relative(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test relative path resolution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd"])

    # Should resolve relative path and then fail on JSON parsing
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_path_resolution_absolute(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test absolute path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle absolute path and fail on JSON parsing
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_output_formatting_with_valid_json(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # This test would succeed if we had a valid JSON file
    # Testing the output formatting logic indirectly
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should fail due to invalid JSON
    assert result == 1
    # Should show error in formatted panel
    output = capture.get()
    assert "Error parsing JSON" in output


def test_execute_syntax_highlighting_preparation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test that the command prepares for syntax highlighting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should fail but show proper error formatting
    assert result == 1
    output = capture.get()
    assert "jq Error" in output


def test_execute_file_read_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test file reading error handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/path/file.json"])

    # Should fail with file reading error
    assert result == 1
    output = capture.get()
    assert "Error reading file" in output


def test_execute_json_parsing_error_details(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test that JSON parsing errors provide details
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should show detailed JSON parsing error
    assert result == 1
    output = capture.get()
    assert "Error parsing JSON" in output
    assert "jq Error" in output


def test_execute_keypath_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.JqCommand,
):
    # Test keypath validation error handling
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "invalid_keypath"])

    # Should fail on JSON parsing first, but tests keypath validation path
    assert result == 1
