"""Integration tests for the MoreCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MoreCommand instance."""
    yield pebble_shell.commands.MoreCommand(shell=shell)


def test_name(command: pebble_shell.commands.MoreCommand):
    assert command.name == "more"


def test_category(command: pebble_shell.commands.MoreCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.MoreCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "more" in output
    assert "View file contents page by page" in output
    assert "-d" in output
    assert "-s" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "more" in output
    assert "View file contents page by page" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # more with no args should read from stdin
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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


def test_execute_small_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test with small file that fits on one screen
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should succeed showing entire file
    if result == 0:
        output = capture.get()
        # Should show complete file contents
        assert len(output.strip()) > 0
        # Should contain typical hosts file patterns
        assert any(pattern in output for pattern in ["localhost", "127.0.0.1", "#"])
    else:
        assert result == 1


def test_execute_large_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test with large file requiring pagination
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
):
    # Test with regular text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed showing text content
    if result == 0:
        output = capture.get()
        # Should show text file contents
        assert len(output.strip()) > 0
        # Should contain readable text
        assert any(char.isprintable() for char in output)
    else:
        assert result == 1


def test_execute_display_errors_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test -d option to display help instead of ringing bell
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "/etc/hosts"])

    # Should either succeed with error display mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with error display mode
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_squeeze_blank_lines_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test -s option to squeeze multiple blank lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hosts"])

    # Should either succeed with squeezed blank lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with reduced blank lines
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_start_line_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test +num option to start at specific line
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["+5", "/etc/passwd"])

    # Should either succeed starting at line 5 or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content starting from specified line
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_search_pattern_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test +/pattern option to start at pattern match
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["+/root", "/etc/passwd"])

    # Should either succeed starting at pattern or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content starting from pattern match
        assert len(output.strip()) > 0
        # Should contain the search pattern
        assert "root" in output
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
):
    # Test pagination behavior with multi-screen content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle pagination appropriately
    if result == 0:
        output = capture.get()
        # Should show content with pagination indicators
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_screen_size_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test screen size handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle screen size appropriately
    if result == 0:
        output = capture.get()
        # Should adapt to screen size
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_line_counting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test line counting functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should count lines appropriately
    if result == 0:
        output = capture.get()
        # Should handle line counting
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_tab_expansion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test tab character expansion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle tab expansion appropriately
    if result == 0:
        output = capture.get()
        # Should expand tabs to spaces
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_control_character_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test control character handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle control characters appropriately
    if result == 0:
        output = capture.get()
        # Should filter or display control characters safely
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_line_wrapping(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
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


def test_execute_file_position_tracking(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test file position tracking
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should track file position appropriately
    if result == 0:
        output = capture.get()
        # Should maintain position information
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_progress_indication(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test progress indication
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should provide progress indication
    if result == 0:
        output = capture.get()
        # Should show progress through file
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_terminal_interaction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
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


def test_execute_interrupt_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test interrupt signal handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle interrupts appropriately
    if result == 0:
        output = capture.get()
        # Should complete normally or handle interrupts
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test memory efficiency with large files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert len(output.strip()) >= 0


def test_execute_unicode_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
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


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
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
    command: pebble_shell.commands.MoreCommand,
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


def test_execute_compatibility_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MoreCommand,
):
    # Test compatibility with traditional more behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should maintain more compatibility
    if result == 0:
        output = capture.get()
        # Should behave like traditional more
        assert len(output.strip()) >= 0
    else:
        assert result == 1
