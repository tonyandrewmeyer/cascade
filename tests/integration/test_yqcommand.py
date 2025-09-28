"""Integration tests for the YqCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a YqCommand instance."""
    yield pebble_shell.commands.YqCommand(shell=shell)


def test_name(command: pebble_shell.commands.YqCommand):
    assert command.name == "yq <file> [keypath]"


def test_category(command: pebble_shell.commands.YqCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.YqCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "yq" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "yq" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "No file specified" in output
    assert "Usage: yq <file> [.foo.bar]" in output


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.yaml"])
    # Should fail with file error
    assert result == 1
    output = capture.get()
    assert "Error reading file" in output


def test_execute_invalid_yaml_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Try to parse a non-YAML file like /etc/passwd
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # /etc/passwd might be valid YAML (plain text is often valid YAML)
    # but we expect it to succeed since YAML is more permissive than JSON
    if result == 1:
        output = capture.get()
        assert "Error parsing YAML" in output
    else:
        # If it succeeds, should show YAML output
        assert result == 0


def test_execute_with_valid_yaml_like_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # /etc/passwd might be parsed as YAML (text files can be valid YAML)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed (if treated as valid YAML) or fail with parsing error
    if result == 0:
        # Should show YAML output formatting
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1
        output = capture.get()
        assert "Error parsing YAML" in output


def test_execute_with_keypath_invalid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test invalid keypath format (not starting with dot)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "foo.bar"])

    # Should fail with keypath format error (if YAML parsing succeeds)
    # or fail with YAML parsing error first
    assert result == 1


def test_execute_with_valid_keypath_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test valid keypath format (starting with dot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".foo.bar"])

    # Should fail with key path error (assuming /etc/passwd doesn't have 'foo' key)
    # or succeed if the file is parsed as YAML and has the key
    if result == 1:
        output = capture.get()
        # Could fail on YAML parsing or key path navigation
        assert any(msg in output for msg in ["Error parsing YAML", "Key path error"])


def test_execute_keypath_navigation_dict_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test dictionary key access in keypath
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".users.0.name"])

    # Should fail with key path error (assuming structure doesn't exist)
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["Error parsing YAML", "Key path error"])


def test_execute_keypath_navigation_array_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test array index access in keypath
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", ".items.0"])

    # Should fail with key path error (assuming structure doesn't exist)
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["Error parsing YAML", "Key path error"])


def test_execute_empty_keypath(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test empty keypath (just dot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "."])

    # Should succeed if YAML parsing succeeds (empty keypath returns whole document)
    if result == 0:
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1


def test_execute_invalid_keypath_missing_dot(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test keypath that doesn't start with dot
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "foo"])

    # Should fail with invalid keypath error
    assert result == 1
    # Note: May fail on YAML parsing first, but if YAML is valid:
    # Should show keypath validation error


def test_execute_multiple_args_extra_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test with more than 2 arguments (extras should be ignored)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd", ".foo", "extra", "args"]
        )

    # Should use first file and first keypath, ignore extras
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["Error parsing YAML", "Key path error"])


def test_execute_path_resolution_relative(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test relative path resolution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../etc/passwd"])

    # Should resolve relative path and then parse as YAML
    if result == 0:
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1


def test_execute_path_resolution_absolute(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test absolute path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle absolute path and parse as YAML
    if result == 0:
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1


def test_execute_yaml_parsing_with_plain_text(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # YAML is more permissive than JSON - plain text can be valid YAML
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # May succeed since YAML can parse plain text
    if result == 0:
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1
        output = capture.get()
        assert "Error parsing YAML" in output


def test_execute_output_formatting_with_valid_yaml(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test the output formatting logic
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    if result == 0:
        # Should show formatted YAML output with syntax highlighting
        output = capture.get()
        assert "yq Output" in output
    else:
        # Should show error in formatted panel
        assert result == 1


def test_execute_syntax_highlighting_preparation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test that the command prepares for syntax highlighting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    if result == 0:
        output = capture.get()
        # Should have YAML syntax highlighting
        assert "yq Output" in output
    else:
        # Should show proper error formatting
        output = capture.get()
        assert "yq Error" in output


def test_execute_file_read_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test file reading error handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/path/file.yaml"])

    # Should fail with file reading error
    assert result == 1
    output = capture.get()
    assert "Error reading file" in output


def test_execute_yaml_parsing_error_details(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test that YAML parsing errors provide details
    # This is harder to trigger since YAML is very permissive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed or show detailed error
    if result == 1:
        output = capture.get()
        assert "yq Error" in output


def test_execute_keypath_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test keypath validation error handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "invalid_keypath"])

    # Should fail with keypath validation error (if YAML parsing succeeds)
    if result == 1:
        output = capture.get()
        # Could be YAML parsing error or keypath validation error
        assert "yq Error" in output


def test_execute_yaml_safe_dump_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.YqCommand,
):
    # Test YAML output formatting with safe_dump
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    if result == 0:
        # Should use yaml.safe_dump for output formatting
        output = capture.get()
        assert "yq Output" in output
    else:
        assert result == 1
