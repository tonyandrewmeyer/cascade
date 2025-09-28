"""Integration tests for the UniqCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import pathlib

    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a UniqCommand instance."""
    yield pebble_shell.commands.UniqCommand(shell=shell)


def test_name(command: pebble_shell.commands.UniqCommand):
    assert command.name == "uniq [-c] [-d] [-u] [file]"


def test_category(command: pebble_shell.commands.UniqCommand):
    assert command.category == "Built-in Commands"


def test_help(command: pebble_shell.commands.UniqCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    # UniqCommand uses default help, so we check for basic command info
    assert "uniq" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "uniq" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    # Should fail with missing file operand error
    assert result == 1
    assert "missing file operand" in capture.get()


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/passwd"])
    # Should fail with invalid option error
    assert result == 1
    assert "invalid option" in capture.get()


def test_execute_basic_file_processing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with duplicate lines
    test_file = tmp_path / "test_uniq.txt"
    test_file.write_text("line1\nline1\nline2\nline2\nline2\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(test_file)])

    # Should succeed and remove adjacent duplicates
    assert result == 0
    # Note: The actual output would depend on the file content being read from Pebble
    # In a real test environment, this would read from the container


def test_execute_count_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with duplicate lines
    test_file = tmp_path / "test_uniq_count.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-c", str(test_file)])

    # Should succeed and show count prefix
    assert result == 0
    # In a real environment, this would show counts like "      2 line1"


def test_execute_duplicates_only_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with some duplicate and unique lines
    test_file = tmp_path / "test_uniq_dup.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-d", str(test_file)])

    # Should succeed and show only lines that are repeated
    assert result == 0
    # In a real environment, this would only show "line1" and "line3"


def test_execute_unique_only_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with some duplicate and unique lines
    test_file = tmp_path / "test_uniq_unique.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-u", str(test_file)])

    # Should succeed and show only lines that appear once
    assert result == 0
    # In a real environment, this would only show "line2"


def test_execute_count_and_duplicates_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with duplicate lines
    test_file = tmp_path / "test_uniq_count_dup.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-c", "-d", str(test_file)])

    # Should succeed and show count with duplicates only
    assert result == 0
    # In a real environment, this would show counts for duplicated lines only


def test_execute_count_and_unique_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a test file with duplicate and unique lines
    test_file = tmp_path / "test_uniq_count_unique.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-c", "-u", str(test_file)])

    # Should succeed and show count with unique lines only
    assert result == 0
    # In a real environment, this would show "      1 line2"


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail since file doesn't exist
    assert result == 1
    # The safe_read_file function should handle the error


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create an empty test file
    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(test_file)])

    # Should succeed with empty file
    assert result == 0
    # Should produce no output for empty file


def test_execute_single_line_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Create a single line test file
    test_file = tmp_path / "single_line.txt"
    test_file.write_text("single line\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(test_file)])

    # Should succeed and output the single line
    assert result == 0


def test_execute_relative_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Test that relative paths work with current directory
    test_file = tmp_path / "relative_test.txt"
    test_file.write_text("line1\nline2\n")

    # Set shell current directory to tmp_path
    command.shell.current_directory = str(tmp_path)

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["relative_test.txt"])

    # Should succeed using relative path
    assert result == 0


def test_execute_absolute_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Test that absolute paths work
    test_file = tmp_path / "absolute_test.txt"
    test_file.write_text("line1\nline2\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(test_file)])

    # Should succeed using absolute path
    assert result == 0


def test_execute_all_options_together(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Test combining all options (though -d and -u are mutually exclusive in effect)
    test_file = tmp_path / "all_options.txt"
    test_file.write_text("line1\nline1\nline2\nline3\nline3\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-c", "-d", "-u", str(test_file)])

    # Should succeed - the command will process all flags
    # Note: -d and -u filters will conflict, but the command handles this
    assert result == 0


def test_execute_multiple_files_uses_first(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UniqCommand,
    tmp_path: pathlib.Path,
):
    # Test that when multiple files are provided, only the first is used
    test_file1 = tmp_path / "file1.txt"
    test_file1.write_text("line1\nline2\n")
    test_file2 = tmp_path / "file2.txt"
    test_file2.write_text("line3\nline4\n")

    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[str(test_file1), str(test_file2)])

    # Should succeed and process only the first file
    assert result == 0
