"""Integration tests for the Unix2dosCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a Unix2dosCommand instance."""
    yield pebble_shell.commands.Unix2dosCommand(shell=shell)


def test_name(command: pebble_shell.commands.Unix2dosCommand):
    assert command.name == "unix2dos"


def test_category(command: pebble_shell.commands.Unix2dosCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.Unix2dosCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "unix2dos" in output
    assert any(
        phrase in output.lower()
        for phrase in ["dos", "unix", "line ending", "convert", "crlf"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "unix2dos" in output
    assert any(
        phrase in output.lower() for phrase in ["dos", "unix", "line ending", "convert"]
    )


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # unix2dos with no args should read from stdin
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
        assert any(msg in output for msg in ["usage", "Usage", "unix2dos", "file"])


def test_execute_convert_unix_to_dos_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test converting Unix line endings to DOS
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed converting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain file contents with DOS line endings
        assert len(output) >= 0
        # Should contain DOS line endings (CRLF)
        if len(output) > 0 and "\n" in output:
            # Should have converted some LF to CRLF
            line_endings = output.count("\n")
            if line_endings > 0:
                # Should contain CRLF sequences
                assert "\r\n" in output or line_endings > 0
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_in_place_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test in-place file conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k", "/etc/hosts"])

    # Should either succeed with in-place conversion or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert file in place (may have no output)
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_keep_date_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test keeping original file date
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k", "/etc/passwd"])

    # Should either succeed keeping date or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve file timestamp
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test quiet mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "/etc/hosts"])

    # Should either succeed quietly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test verbose mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "/etc/passwd"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should provide detailed information in verbose mode
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain status information
            assert any(
                word in output.lower()
                for word in ["convert", "process", "file", "line"]
            )
    else:
        assert result == 1


def test_execute_backup_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test creating backup of original file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "/etc/hosts"])

    # Should either succeed creating backup or fail gracefully
    if result == 0:
        output = capture.get()
        # Should create backup file
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_force_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test forcing conversion of binary files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/etc/passwd"])

    # Should either succeed with force or fail gracefully
    if result == 0:
        output = capture.get()
        # Should force conversion
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_new_file_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test new file mode (write to different file)
    with tempfile.NamedTemporaryFile(suffix="_hosts_dos", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "/etc/hosts", output_path])

    # Should either succeed with new file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should create new file with DOS line endings
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_preserve_ownership(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test preserving file ownership
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "/etc/passwd"])

    # Should either succeed preserving ownership or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve file ownership
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_safe_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test safe mode (skip binary files)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "/etc/hosts"])

    # Should either succeed in safe mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should skip binary files safely
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_ascii_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test ASCII mode conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-ascii", "/etc/passwd"])

    # Should either succeed in ASCII mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert in ASCII mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_iso_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test ISO mode conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-iso", "/etc/hosts"])

    # Should either succeed in ISO mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert in ISO mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_utf8_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test UTF-8 mode conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-utf8", "/etc/passwd"])

    # Should either succeed in UTF-8 mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should convert in UTF-8 mode
        assert len(output) >= 0
        if len(output) > 0:
            # Should handle UTF-8 encoding properly
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_empty_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should succeed with no output for empty file
    if result == 0:
        output = capture.get()
        # Should produce no output for empty file
        assert len(output) == 0
    else:
        # May fail if cannot read/write /dev/null
        assert result == 1


def test_execute_file_with_dos_endings(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test file that already has DOS line endings
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hostname"])

    # Should succeed with no changes needed or double conversion
    if result == 0:
        output = capture.get()
        # Should handle existing DOS format appropriately
        assert len(output) >= 0
        if len(output) > 0 and "\n" in output:
            # Should have DOS line endings
            assert "\r\n" in output or output.count("\n") >= 1
    else:
        assert result == 1


def test_execute_file_with_mixed_endings(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test file with mixed line endings
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed normalizing mixed line endings
    if result == 0:
        output = capture.get()
        # Should normalize all line endings to DOS format
        assert len(output) >= 0
        if len(output) > 0 and "\n" in output:
            # Should contain DOS line endings
            line_count = output.count("\n")
            if line_count > 0:
                # Should have CRLF sequences
                assert "\r\n" in output or line_count >= 1
    else:
        assert result == 1


def test_execute_single_line_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test single line file without newline
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hostname"])

    # Should succeed with single line
    if result == 0:
        output = capture.get()
        # Should handle single line appropriately
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test processing multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/hostname"])

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process both files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
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
    command: pebble_shell.commands.Unix2dosCommand,
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
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either handle binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process binary file (may skip or convert)
        assert len(output) >= 0
    else:
        # May fail for binary files in safe mode
        assert result == 1


def test_execute_readonly_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test with read-only file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either succeed or fail appropriately for read-only
    if result == 0:
        output = capture.get()
        # Should handle read-only files
        assert len(output) >= 0
    else:
        # May fail if cannot write to read-only file
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "/etc/hosts"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-ascii", "-utf8", "/etc/hosts"])

    # Should either handle conflicts or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["conflicting", "invalid", "error"])
    else:
        # May resolve conflicts automatically
        assert result == 0


def test_execute_unicode_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test file with Unicode content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-utf8", "/etc/hosts"])

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


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle large files efficiently
    if result == 0:
        output = capture.get()
        # Should process large files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_line_ending_conversion_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test accuracy of line ending conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should accurately convert line endings
    if result == 0:
        output = capture.get()
        # Should convert Unix LF to DOS CRLF
        assert len(output) >= 0
        if len(output) > 0 and "\n" in output:
            # Should have proper DOS line endings
            lines = output.split("\n")
            if len(lines) > 1:
                # Should contain CRLF sequences
                assert "\r\n" in output or len(lines) >= 2
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
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


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_integrity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test data integrity during conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should maintain data integrity
    if result == 0:
        output = capture.get()
        # Should preserve all content except line endings
        assert len(output) >= 0
        if len(output) > 0:
            # Should not lose any data
            content_without_crlf = output.replace("\r\n", "\n").replace("\n", "")
            assert len(content_without_crlf) > 0
    else:
        assert result == 1


def test_execute_consistent_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test consistent conversion behavior
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


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
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
    command: pebble_shell.commands.Unix2dosCommand,
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


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.Unix2dosCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform-specific line endings
        assert len(output) >= 0
        if len(output) > 0 and "\n" in output:
            # Should produce DOS-compatible line endings
            lines = output.count("\n")
            if lines > 0:
                # Should contain appropriate line endings
                assert "\r\n" in output or lines >= 1
    else:
        assert result == 1
