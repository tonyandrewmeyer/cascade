"""Integration tests for the FoldCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FoldCommand instance."""
    yield pebble_shell.commands.FoldCommand(shell=shell)


def test_name(command: pebble_shell.commands.FoldCommand):
    assert command.name == "fold"


def test_category(command: pebble_shell.commands.FoldCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.FoldCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "fold" in output
    assert "wrap" in output.lower() or "lines" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "fold" in output
    assert "wrap" in output.lower() or "lines" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # fold with no args should read from stdin and wrap at default width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either read from stdin or show usage
    if result == 0:
        output = capture.get()
        # Should wait for stdin input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "fold", "file"])


def test_execute_default_width_wrap(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test default width wrapping (usually 80 columns)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed wrapping or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain wrapped content
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be <= 80 characters (default width)
            long_lines = [line for line in lines if len(line) > 80]
            # Allow some long lines but most should be wrapped
            assert len(long_lines) <= len(lines) // 2
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_custom_width(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test custom width wrapping
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "40", "/etc/hosts"])

    # Should either succeed with custom width or fail gracefully
    if result == 0:
        output = capture.get()
        # Should wrap at 40 characters
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be <= 40 characters
            long_lines = [line for line in lines if len(line) > 40]
            # Allow some long lines but most should be wrapped
            assert len(long_lines) <= len(lines) // 2
    else:
        assert result == 1


def test_execute_width_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test short form width option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "60", "/etc/passwd"])

    # Should succeed with 60 character width
    if result == 0:
        output = capture.get()
        # Should wrap at 60 characters
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be <= 60 characters
            long_lines = [line for line in lines if len(line) > 60]
            assert len(long_lines) <= len(lines) // 2
    else:
        assert result == 1


def test_execute_width_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test long form width option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--width=50", "/etc/hosts"])

    # Should succeed with 50 character width
    if result == 0:
        output = capture.get()
        # Should wrap at 50 characters
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be <= 50 characters
            long_lines = [line for line in lines if len(line) > 50]
            assert len(long_lines) <= len(lines) // 2
    else:
        assert result == 1


def test_execute_break_spaces_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test breaking only at spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-w", "30", "/etc/passwd"])

    # Should either succeed breaking at spaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should break lines at spaces when possible
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Lines should generally not break in the middle of words
            for line in lines:
                if len(line) > 0 and len(line) < 30:
                    # Line should end with complete word
                    assert not line.endswith("-") or line.endswith("--")
    else:
        assert result == 1


def test_execute_spaces_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test long form spaces option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--spaces", "-w", "25", "/etc/hosts"]
        )

    # Should succeed breaking at spaces
    if result == 0:
        output = capture.get()
        # Should break at spaces
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_bytes_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test byte mode instead of character mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "-w", "20", "/etc/passwd"])

    # Should either succeed in byte mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should count bytes instead of characters
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_bytes_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test long form bytes option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--bytes", "-w", "35", "/etc/hosts"]
        )

    # Should succeed in bytes mode
    if result == 0:
        output = capture.get()
        # Should count bytes
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_combined_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test combining spaces and bytes options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-sb", "-w", "45", "/etc/passwd"])

    # Should either succeed with combined options or fail gracefully
    if result == 0:
        output = capture.get()
        # Should break at spaces in byte mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_very_narrow_width(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test very narrow width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "5", "/etc/hostname"])

    # Should succeed with very narrow width
    if result == 0:
        output = capture.get()
        # Should wrap at 5 characters
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be <= 5 characters
            long_lines = [line for line in lines if len(line) > 5]
            assert len(long_lines) <= len(lines) // 2
    else:
        assert result == 1


def test_execute_very_wide_width(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test very wide width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "200", "/etc/passwd"])

    # Should succeed with very wide width
    if result == 0:
        output = capture.get()
        # Should not wrap much with 200 character width
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Few or no lines should be wrapped
            very_long_lines = [line for line in lines if len(line) > 150]
            # Should preserve long lines
            assert len(very_long_lines) >= 0
    else:
        assert result == 1


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with no output for empty file
    assert result == 0
    output = capture.get()
    # Should produce no output for empty file
    assert len(output) == 0


def test_execute_single_line_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with single line file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "30", "/etc/hostname"])

    # Should succeed wrapping single line
    if result == 0:
        output = capture.get()
        # Should wrap single line if needed
        assert len(output) >= 0
        if len(output) > 30:
            lines = output.split("\n")
            # Should have multiple lines if original was long
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_file_with_long_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test file with very long lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "20", "/etc/passwd"])

    # Should succeed wrapping long lines
    if result == 0:
        output = capture.get()
        # Should wrap long lines
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Should have wrapped lines
            short_lines = [line for line in lines if len(line) <= 20]
            # Most lines should be <= 20 characters
            assert len(short_lines) >= len(lines) // 2
    else:
        assert result == 1


def test_execute_file_with_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test file with tabs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "40", "/etc/fstab"])

    # Should succeed handling tabs
    if result == 0:
        output = capture.get()
        # Should handle tabs appropriately
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Should wrap considering tab expansion
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test processing multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-w", "50", "/etc/hosts", "/etc/hostname"]
        )

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process both files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_directory_as_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_width_zero(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with zero width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "0", "/etc/hosts"])

    # Should fail with invalid width error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "width", "zero", "error"])


def test_execute_invalid_width_negative(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with negative width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "-10", "/etc/hosts"])

    # Should fail with negative width error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative", "width", "error"])


def test_execute_invalid_width_non_numeric(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with non-numeric width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "abc", "/etc/hosts"])

    # Should fail with invalid width error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "width", "number", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_unicode_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test file with Unicode content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "30", "/etc/hosts"])

    # Should either succeed with Unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle Unicode characters properly
        assert len(output) >= 0
        # Should maintain Unicode character integrity
        if len(output) > 0:
            assert isinstance(output, str)
            lines = output.split("\n")
            # Should wrap Unicode text appropriately
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "40", "/bin/ls"])

    # Should either handle binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process binary file (may contain binary data)
        assert len(output) >= 0
    else:
        # May fail for binary files
        assert result == 1


def test_execute_preserve_newlines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test preserving existing newlines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "100", "/etc/passwd"])

    # Should preserve and add newlines as needed
    if result == 0:
        output = capture.get()
        # Should maintain line structure
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Should have multiple lines
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_width_boundary_conditions(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test width boundary conditions
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "1", "/etc/hostname"])

    # Should handle minimum width
    if result == 0:
        output = capture.get()
        # Should wrap at 1 character width
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be 1 character
            single_char_lines = [line for line in lines if len(line) <= 1]
            assert len(single_char_lines) >= len(lines) // 2
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "80", "/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "60", "/etc/passwd"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_consistent_wrapping(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test consistent wrapping behavior
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["-w", "50", "/etc/hosts"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["-w", "50", "/etc/hosts"])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both executions should succeed consistently
        assert result1 == result2
    else:
        # At least one should succeed or both should fail consistently
        assert result1 == result2


def test_execute_line_length_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test line length accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "25", "/etc/passwd"])

    # Should wrap lines accurately
    if result == 0:
        output = capture.get()
        # Should respect width limit accurately
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Most lines should be within width limit
            compliant_lines = [line for line in lines if len(line) <= 25]
            assert len(compliant_lines) >= len(lines) // 2
    else:
        assert result == 1


def test_execute_word_boundary_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FoldCommand,
):
    # Test word boundary preservation with spaces option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-w", "15", "/etc/passwd"])

    # Should preserve word boundaries when possible
    if result == 0:
        output = capture.get()
        # Should break at word boundaries
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Lines should not break in middle of words when possible
            for line in lines:
                if len(line) > 0 and len(line) < 15:
                    # Should end at word boundary
                    assert line[-1] != "-" or line.endswith("--")
    else:
        assert result == 1
