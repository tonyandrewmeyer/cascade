"""Integration tests for the DirnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DirnameCommand instance."""
    yield pebble_shell.commands.DirnameCommand(shell=shell)


def test_name(command: pebble_shell.commands.DirnameCommand):
    assert command.name == "dirname"


def test_category(command: pebble_shell.commands.DirnameCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.DirnameCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "dirname" in output
    assert "Strip last component from file name" in output
    assert "/usr/bin/sort" in output
    assert "stdio.h" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "dirname" in output
    assert "Strip last component from file name" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # dirname with no args should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing operand error
    assert result == 1
    output = capture.get()
    assert "missing operand" in output


def test_execute_absolute_path_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with absolute path containing file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/sort"])

    # Should succeed and return directory part
    assert result == 0
    output = capture.get().strip()
    assert output == "/usr/bin"


def test_execute_absolute_path_with_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with absolute path to directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin/"])

    # Should succeed and return parent directory
    assert result == 0
    output = capture.get().strip()
    assert output == "/usr"


def test_execute_relative_path_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with relative path containing file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["dir/file.txt"])

    # Should succeed and return directory part
    assert result == 0
    output = capture.get().strip()
    assert output == "dir"


def test_execute_filename_only_no_slash(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with filename only (no slash)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stdio.h"])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_root_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with root directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should succeed and return root
    assert result == 0
    output = capture.get().strip()
    assert output == "/"


def test_execute_root_with_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with file in root directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/file.txt"])

    # Should succeed and return root
    assert result == 0
    output = capture.get().strip()
    assert output == "/"


def test_execute_trailing_slashes_removal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with trailing slashes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/bin///"])

    # Should succeed and remove trailing slashes
    assert result == 0
    output = capture.get().strip()
    assert output == "/usr"


def test_execute_multiple_paths(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with multiple paths
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/usr/bin/sort", "/etc/passwd", "file.txt"]
        )

    # Should succeed and return dirname for each path
    assert result == 0
    output = capture.get().strip()
    lines = output.split("\n")
    assert len(lines) == 3
    assert lines[0] == "/usr/bin"
    assert lines[1] == "/etc"
    assert lines[2] == "."


def test_execute_nested_deep_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with deeply nested path
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/very/deep/nested/path/file.txt"]
        )

    # Should succeed and return parent directory
    assert result == 0
    output = capture.get().strip()
    assert output == "/very/deep/nested/path"


def test_execute_relative_nested_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with relative nested path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["dir1/dir2/dir3/file"])

    # Should succeed and return directory part
    assert result == 0
    output = capture.get().strip()
    assert output == "dir1/dir2/dir3"


def test_execute_current_directory_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with current directory reference
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["./file.txt"])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_parent_directory_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with parent directory reference
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../file.txt"])

    # Should succeed and return parent reference
    assert result == 0
    output = capture.get().strip()
    assert output == ".."


def test_execute_complex_relative_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with complex relative path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../../dir/file"])

    # Should succeed and return directory part
    assert result == 0
    output = capture.get().strip()
    assert output == "../../dir"


def test_execute_empty_string_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with empty string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_single_slash(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with single slash
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/"])

    # Should succeed and return root
    assert result == 0
    output = capture.get().strip()
    assert output == "/"


def test_execute_multiple_slashes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with multiple consecutive slashes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr//bin//file"])

    # Should succeed and handle multiple slashes
    assert result == 0
    output = capture.get().strip()
    assert output == "/usr//bin"


def test_execute_path_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with path containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/path with spaces/file.txt"])

    # Should succeed and handle spaces
    assert result == 0
    output = capture.get().strip()
    assert output == "/path with spaces"


def test_execute_path_with_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with path containing special characters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/dir-with_special.chars/file@name"]
        )

    # Should succeed and handle special characters
    assert result == 0
    output = capture.get().strip()
    assert output == "/dir-with_special.chars"


def test_execute_just_filename_extension(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with just filename and extension
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["file.extension"])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_hidden_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with hidden file (starts with dot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dir/.hidden"])

    # Should succeed and return directory
    assert result == 0
    output = capture.get().strip()
    assert output == "/dir"


def test_execute_hidden_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with hidden directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/parent/.hidden/file"])

    # Should succeed and return hidden directory
    assert result == 0
    output = capture.get().strip()
    assert output == "/parent/.hidden"


def test_execute_dot_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with just dot (current directory)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["."])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_dotdot_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with just double dot (parent directory)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[".."])

    # Should succeed and return current directory
    assert result == 0
    output = capture.get().strip()
    assert output == "."


def test_execute_long_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with very long path
    long_path = "/very/long/path/with/many/components/that/goes/deep/into/filesystem/structure/file.txt"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_path])

    # Should succeed and return directory part
    assert result == 0
    output = capture.get().strip()
    expected = (
        "/very/long/path/with/many/components/that/goes/deep/into/filesystem/structure"
    )
    assert output == expected


def test_execute_mixed_path_types(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DirnameCommand,
):
    # Test with mix of different path types
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "/absolute/path/file",
                "relative/path/file",
                "just_filename",
                "/",
                ".",
            ],
        )

    # Should succeed and handle all path types
    assert result == 0
    output = capture.get().strip()
    lines = output.split("\n")
    assert len(lines) == 5
    assert lines[0] == "/absolute/path"
    assert lines[1] == "relative/path"
    assert lines[2] == "."
    assert lines[3] == "/"
    assert lines[4] == "."
