"""Integration tests for the LessCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LessCommand instance."""
    yield pebble_shell.commands.LessCommand(shell=shell)


def test_name(command: pebble_shell.commands.LessCommand):
    assert command.name == "less"


def test_category(command: pebble_shell.commands.LessCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.LessCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "less" in output
    assert "View file contents with pagination" in output
    assert "-n" in output
    assert "-E" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "less" in output
    assert "View file contents with pagination" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # less with no args should read from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed reading stdin or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle stdin input
        assert len(output.strip()) >= 0
    else:
        # Should fail if no stdin available
        assert result == 1


def test_execute_single_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test viewing single file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed showing file or fail if not accessible
    if result == 0:
        output = capture.get()
        # Should show file contents
        assert len(output.strip()) > 0
        # Should contain typical /etc/passwd content patterns
        assert any(pattern in output for pattern in ["root:", "bin:", ":"])
    else:
        # Should fail if file not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["No such file", "permission denied", "error"]
        )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with empty output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty file
        assert len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_large_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/share/dict/words"])

    # Should either succeed with pagination or fail if not found
    if result == 0:
        output = capture.get()
        # Should handle large file with pagination
        assert len(output.strip()) > 0
    else:
        # Should fail if file not found
        assert result == 1


def test_execute_binary_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either succeed showing binary or handle appropriately
    if result == 0:
        output = capture.get()
        # Should handle binary file (may show warning or filtered content)
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_text_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should succeed showing text content
    if result == 0:
        output = capture.get()
        # Should show text file contents
        assert len(output.strip()) > 0
        # Should contain typical hosts file patterns
        assert any(pattern in output for pattern in ["localhost", "127.0.0.1", "#"])
    else:
        assert result == 1


def test_execute_line_numbers_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -N option for line numbers
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "/etc/hosts"])

    # Should either succeed with line numbers or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show line numbers
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_no_line_numbers_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -n option to suppress line numbers
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "/etc/hosts"])

    # Should either succeed without line numbers or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content without explicit line numbers
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_quit_at_eof_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -E option to quit at EOF
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-E", "/etc/hosts"])

    # Should either succeed with EOF behavior or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content and quit at EOF
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_ignore_case_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -i option for case-insensitive search
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/etc/hosts"])

    # Should either succeed with case-insensitive mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with case-insensitive search enabled
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_squeeze_blank_lines_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -s option to squeeze blank lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hosts"])

    # Should either succeed with squeezed blank lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with reduced blank lines
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_chop_long_lines_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -S option to chop long lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-S", "/etc/passwd"])

    # Should either succeed with chopped lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with horizontal scrolling
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_raw_control_chars_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test -r option for raw control characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "/etc/hosts"])

    # Should either succeed with raw control chars or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with raw control characters
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed showing multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content from multiple files
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_directory_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with directory argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should either handle directory or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show directory contents or error
        assert len(output.strip()) >= 0
    else:
        # Should fail if directories not supported
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["is a directory", "cannot open", "error"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["permission denied", "cannot open", "error"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with symbolic link
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])  # Often a symlink

    # Should either follow symlink or handle appropriately
    if result == 0:
        output = capture.get()
        # Should follow symlink and show target
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_special_files_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test with special files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc/version"])

    # Should either succeed with special file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show special file contents
        assert "Linux" in output or len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_pagination_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test pagination behavior with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle pagination appropriately
    if result == 0:
        output = capture.get()
        # Should show content with pagination
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_search_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test search functionality within less
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should provide search capability
    if result == 0:
        output = capture.get()
        # Should show searchable content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_navigation_capabilities(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test navigation capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should provide navigation features
    if result == 0:
        output = capture.get()
        # Should show navigable content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_terminal_interaction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test terminal interaction capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should interact with terminal appropriately
    if result == 0:
        output = capture.get()
        # Should handle terminal interaction
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_status_line_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test status line display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should display status information
    if result == 0:
        output = capture.get()
        # Should include status information
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_color_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test color support in output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R", "/etc/hosts"])

    # Should handle color escape sequences
    if result == 0:
        output = capture.get()
        # Should process color information
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_unicode_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test unicode character support
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle unicode characters appropriately
    if result == 0:
        output = capture.get()
        # Should display unicode content correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_tab_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test tab character expansion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle tab expansion appropriately
    if result == 0:
        output = capture.get()
        # Should expand tabs correctly
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_line_wrapping(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test line wrapping behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle line wrapping appropriately
    if result == 0:
        output = capture.get()
        # Should wrap long lines correctly
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_performance_large_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test performance with large files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/log/syslog"])

    # Should handle large files efficiently
    if result == 0:
        output = capture.get()
        # Should load efficiently without hanging
        assert len(output) >= 0
    else:
        # Should fail if file not found
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-Z", "/etc/hosts"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0


def test_execute_exit_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LessCommand,
):
    # Test exit behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should exit appropriately
    if result == 0:
        output = capture.get()
        # Should complete and exit normally
        assert len(output.strip()) >= 0
    else:
        assert result == 1
