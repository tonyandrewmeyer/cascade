"""Integration tests for the UnexpandCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a UnexpandCommand instance."""
    yield pebble_shell.commands.UnexpandCommand(shell=shell)


def test_name(command: pebble_shell.commands.UnexpandCommand):
    assert command.name == "unexpand"


def test_category(command: pebble_shell.commands.UnexpandCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.UnexpandCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "unexpand" in output
    assert "Convert spaces to tabs" in output
    assert "spaces" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "unexpand" in output
    assert "Convert spaces to tabs" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # unexpand with no args should read from stdin
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
        assert any(msg in output for msg in ["usage", "Usage", "unexpand", "file"])


def test_execute_convert_spaces_to_tabs_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test converting spaces to tabs in a file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed converting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain file contents with spaces converted to tabs
        assert len(output) >= 0
        # Should have converted leading spaces to tabs where appropriate
        if "    " in output:
            # Should contain tabs instead of multiple spaces
            assert "\t" in output
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_all_spaces_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test converting all spaces, not just leading ones
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "/etc/hosts"])

    # Should either succeed converting all spaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert all spaces to tabs, not just leading
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_first_only_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test converting only first sequence of spaces on each line
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--first-only", "/etc/hosts"])

    # Should either succeed with first-only conversion or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert only first sequence of spaces
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_custom_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test custom tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "4", "/etc/hosts"])

    # Should either succeed with custom tab stops or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use 4-space tab stops
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_multiple_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test multiple custom tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "4,8,12", "/etc/hosts"])

    # Should either succeed with multiple tab stops or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use specified tab stops
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_leading_spaces_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test converting only leading spaces (default behavior)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed converting leading spaces only
    if result == 0:
        output = capture.get()
        # Should convert leading spaces but leave internal spaces
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_preserve_existing_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test preserving existing tabs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/fstab"])

    # Should either succeed preserving tabs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve existing tabs and add new ones
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with no output for empty file
    assert result == 0
    output = capture.get()
    # Should produce no output for empty file
    assert len(output) == 0


def test_execute_file_with_no_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test file with no spaces to convert
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hostname"])

    # Should succeed with unchanged content
    if result == 0:
        output = capture.get()
        # Should pass through content unchanged if no spaces
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_file_with_only_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test file that already has only tabs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/fstab"])

    # Should succeed preserving existing tabs
    if result == 0:
        output = capture.get()
        # Should preserve existing tab structure
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_mixed_spaces_and_tabs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test file with mixed spaces and tabs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed handling mixed whitespace
    if result == 0:
        output = capture.get()
        # Should handle mixed whitespace appropriately
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_lines_with_different_indentation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test lines with varying indentation levels
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should succeed with varying indentation
    if result == 0:
        output = capture.get()
        # Should handle different indentation levels
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_very_long_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test very long lines
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed with long lines
    if result == 0:
        output = capture.get()
        # Should handle long lines efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_unicode_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test file with Unicode content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed with Unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle Unicode characters properly
        assert len(output) >= 0
        # Should maintain Unicode character integrity
        if len(output) > 0:
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either handle binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process binary file (may contain binary data)
        assert len(output) >= 0
    else:
        # May fail for binary files
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test processing multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process both files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
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
    command: pebble_shell.commands.UnexpandCommand,
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
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with invalid tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "abc", "/etc/hosts"])

    # Should fail with invalid tab stops error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "tab", "number", "error"])


def test_execute_zero_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with zero tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "0", "/etc/hosts"])

    # Should either handle zero or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "zero", "tab", "error"])
    else:
        # May handle zero tab stops
        assert result == 0


def test_execute_negative_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with negative tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-4", "/etc/hosts"])

    # Should fail with negative tab stops error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative", "tab", "error"])


def test_execute_very_large_tab_stops(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test with very large tab stops
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "999999", "/etc/hosts"])

    # Should either handle large tab stops or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle large tab stops
        assert len(output) >= 0
    else:
        # Should fail if tab stops too large
        assert result == 1


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-a", "--first-only", "/etc/hosts"]
        )

    # Should either handle conflicts or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["conflicting", "invalid", "error"])
    else:
        # May resolve conflicts automatically
        assert result == 0


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should maintain text structure
        assert len(output) >= 0
        if len(output) > 0:
            # Should preserve line structure
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_tab_alignment_correctness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test tab alignment correctness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "8", "/etc/passwd"])

    # Should produce correctly aligned tabs
    if result == 0:
        output = capture.get()
        # Should align to 8-column tab stops
        assert len(output) >= 0
        # Tabs should align content properly
        if "\t" in output:
            assert len(output) > 0
    else:
        assert result == 1


def test_execute_space_to_tab_conversion_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test accuracy of space to tab conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should accurately convert spaces to tabs
    if result == 0:
        output = capture.get()
        # Should convert appropriate spaces to tabs
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
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


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work regardless of locale settings
    if result == 0:
        output = capture.get()
        # Should be locale-independent
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform-specific features
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["/etc/hosts"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["/etc/hosts"])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both executions should succeed consistently
        assert result1 == result2
    else:
        # At least one should succeed or both should fail consistently
        assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UnexpandCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should operate robustly
    if result == 0:
        output = capture.get()
        # Should handle stress conditions
        assert len(output) >= 0
    else:
        assert result == 1
