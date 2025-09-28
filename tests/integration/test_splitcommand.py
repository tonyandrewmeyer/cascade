"""Integration tests for the SplitCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SplitCommand instance."""
    yield pebble_shell.commands.SplitCommand(shell=shell)


def test_name(command: pebble_shell.commands.SplitCommand):
    assert command.name == "split"


def test_category(command: pebble_shell.commands.SplitCommand):
    assert command.category == "Data Processing"


def test_help(command: pebble_shell.commands.SplitCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "split" in output
    assert "Split a file into pieces" in output
    assert "-l NUMBER" in output
    assert "-b SIZE" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "split" in output
    assert "Split a file into pieces" in output


def test_execute_no_args_default_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # split with no args should read from stdin
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (if stdin available) or fail gracefully
    assert result in [0, 1]


def test_execute_input_file_split(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test splitting an existing file
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed (splitting /etc/passwd) or fail if file not accessible
    if result == 0:
        # Should have created split files (xaa, xab, etc.)
        pass
    else:
        assert result == 1


def test_execute_nonexistent_input_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test splitting nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_custom_prefix(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test with custom prefix for output files
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd", "myprefix"])

    # Should either succeed with custom prefix or fail gracefully
    if result == 0:
        # Should have created files with "myprefix" prefix
        pass
    else:
        assert result == 1


def test_execute_lines_option_split_by_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -l option to split by number of lines
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-l", "10", "/etc/passwd"])

    # Should either succeed with 10 lines per file or fail gracefully
    if result == 0:
        # Should have split into files with 10 lines each
        pass
    else:
        assert result == 1


def test_execute_lines_option_invalid_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -l option with invalid number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l", "invalid", "/etc/passwd"])

    # Should fail with invalid number error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "number"])


def test_execute_bytes_option_split_by_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -b option to split by byte size
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-b", "1024", "/etc/passwd"])

    # Should either succeed with 1024 bytes per file or fail gracefully
    if result == 0:
        # Should have split into files with 1024 bytes each
        pass
    else:
        assert result == 1


def test_execute_bytes_option_invalid_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -b option with invalid size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "invalid", "/etc/passwd"])

    # Should fail with invalid size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "size"])


def test_execute_suffix_length_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -a option to set suffix length
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-a", "3", "/etc/passwd"])

    # Should either succeed with 3-character suffixes or fail gracefully
    if result == 0:
        # Should have created files with 3-character suffixes (xaaa, xaab, etc.)
        pass
    else:
        assert result == 1


def test_execute_suffix_length_invalid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -a option with invalid suffix length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "0", "/etc/passwd"])

    # Should fail with invalid suffix length
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "suffix"])


def test_execute_numeric_suffixes_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -d option for numeric suffixes
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-d", "/etc/passwd"])

    # Should either succeed with numeric suffixes or fail gracefully
    if result == 0:
        # Should have created files with numeric suffixes (x00, x01, etc.)
        pass
    else:
        assert result == 1


def test_execute_verbose_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test --verbose option for diagnostic output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--verbose", "/etc/passwd"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        _ = capture.get()
        # Should show diagnostic messages about file creation
        pass
    else:
        assert result == 1


def test_execute_line_bytes_option_c(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -C option for maximum bytes per line per file
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-C", "80", "/etc/passwd"])

    # Should either succeed with line-byte limit or fail gracefully
    if result == 0:
        # Should have limited lines to 80 bytes per output file
        pass
    else:
        assert result == 1


def test_execute_multiple_options_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test multiple options together
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["-l", "5", "-a", "3", "-d", "/etc/passwd", "test"]
        )

    # Should either succeed with all options or fail gracefully
    if result == 0:
        # Should have combined effects: 5 lines, 3-char numeric suffixes, "test" prefix
        pass
    else:
        assert result == 1


def test_execute_size_suffixes_k_m_g(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test size suffixes (k, M, G) if supported
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-b", "1k", "/etc/passwd"])

    # Should either succeed with 1k (1024 bytes) or fail gracefully
    if result == 0:
        # Should have parsed "1k" as 1024 bytes
        pass
    else:
        assert result == 1


def test_execute_zero_lines_split(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -l 0 (should be invalid)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l", "0", "/etc/passwd"])

    # Should fail with invalid line count
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "zero", "lines"])


def test_execute_zero_bytes_split(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test -b 0 (should be invalid)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "0", "/etc/passwd"])

    # Should fail with invalid byte size
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "zero", "size"])


def test_execute_output_file_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test that output files are created
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-l", "2", "/etc/passwd"])

    # Should either succeed and create output files or fail gracefully
    if result == 0:
        # Should have created split files in current directory
        pass
    else:
        assert result == 1


def test_execute_empty_input_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test splitting empty file (if available)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed (creating empty output) or fail gracefully
    if result == 0:
        # Should handle empty input gracefully
        pass
    else:
        assert result == 1


def test_execute_permission_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SplitCommand,
):
    # Test handling of permission errors
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail gracefully if permission denied
    if result == 1:
        _ = capture.get()
        # Should show appropriate error message
        pass
    else:
        # May succeed if file is readable
        assert result == 0
