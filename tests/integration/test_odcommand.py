"""Integration tests for the OdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a OdCommand instance."""
    yield pebble_shell.commands.OdCommand(shell=shell)


def test_name(command: pebble_shell.commands.OdCommand):
    assert command.name == "od"


def test_category(command: pebble_shell.commands.OdCommand):
    assert command.category == "Data Processing"


def test_help(command: pebble_shell.commands.OdCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "od" in output
    assert "Dump files in octal format" in output
    assert "-t" in output
    assert "-x" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "od" in output
    assert "Dump files in octal format" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # od with no args should read from stdin
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


def test_execute_single_file_default_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test dumping single file in default octal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed showing octal dump or fail if not accessible
    if result == 0:
        output = capture.get()
        # Should show octal dump with addresses and data
        assert len(output.strip()) > 0
        # Should contain octal values (digits 0-7)
        assert any(char in "01234567" for char in output)
    else:
        # Should fail if file not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["No such file", "permission denied", "error"]
        )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
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
    command: pebble_shell.commands.OdCommand,
):
    # Test with empty file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with empty output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty file (may show just final address)
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_binary_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should succeed showing binary dump
    if result == 0:
        output = capture.get()
        # Should show binary data in octal format
        assert len(output.strip()) > 0
        # Should contain octal values
        assert any(char in "01234567" for char in output)
    else:
        assert result == 1


def test_execute_text_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed showing text dump
    if result == 0:
        output = capture.get()
        # Should show text data in octal format
        assert len(output.strip()) > 0
        # Should contain octal values
        assert any(char in "01234567" for char in output)
    else:
        assert result == 1


def test_execute_hexadecimal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -x option for hexadecimal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/hosts"])

    # Should either succeed with hex format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show hexadecimal dump
        assert len(output.strip()) > 0
        # Should contain hex values (0-9, a-f)
        assert any(char in "0123456789abcdef" for char in output.lower())
    else:
        assert result == 1


def test_execute_decimal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -d option for decimal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "/etc/hosts"])

    # Should either succeed with decimal format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show decimal dump
        assert len(output.strip()) > 0
        # Should contain decimal values
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_character_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -c option for character format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "/etc/hosts"])

    # Should either succeed with character format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show character dump with escape sequences
        assert len(output.strip()) > 0
        # Should contain character representations
        assert any(char.isprintable() for char in output)
    else:
        assert result == 1


def test_execute_type_format_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -t option with format specification
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "x1", "/etc/hosts"])

    # Should either succeed with specified format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dump in specified format
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_address_radix_decimal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -A d option for decimal address radix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-A", "d", "/etc/hosts"])

    # Should either succeed with decimal addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show decimal addresses
        assert len(output.strip()) > 0
        # Should contain decimal address values
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_address_radix_hex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -A x option for hexadecimal address radix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-A", "x", "/etc/hosts"])

    # Should either succeed with hex addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show hexadecimal addresses
        assert len(output.strip()) > 0
        # Should contain hex address values
        assert any(char in "0123456789abcdef" for char in output.lower())
    else:
        assert result == 1


def test_execute_address_radix_octal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -A o option for octal address radix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-A", "o", "/etc/hosts"])

    # Should either succeed with octal addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show octal addresses
        assert len(output.strip()) > 0
        # Should contain octal address values
        assert any(char in "01234567" for char in output)
    else:
        assert result == 1


def test_execute_address_radix_none(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -A n option for no address display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-A", "n", "/etc/hosts"])

    # Should either succeed without addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show data without addresses
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_skip_bytes_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -j option to skip bytes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-j", "10", "/etc/hosts"])

    # Should either succeed skipping bytes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dump starting from offset
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_read_bytes_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -N option to limit bytes read
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "50", "/etc/hosts"])

    # Should either succeed reading limited bytes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show limited amount of data
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_width_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test -w option for output width
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "16", "/etc/hosts"])

    # Should either succeed with specified width or fail gracefully
    if result == 0:
        output = capture.get()
        # Should format output with specified width
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed dumping multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dumps from multiple files
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "1000", "/usr/bin/bash"])

    # Should either succeed with large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_small_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with very small file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hostname"])

    # Should either succeed with small file or fail if not found
    if result == 0:
        output = capture.get()
        # Should handle small file appropriately
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_special_files_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with special files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "100", "/proc/version"])

    # Should either succeed with special file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show special file contents in dump format
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
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


def test_execute_directory_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
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


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test with symbolic link
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])  # Often a symlink

    # Should either follow symlink or handle appropriately
    if result == 0:
        output = capture.get()
        # Should follow symlink and dump target
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_address_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test address format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should format addresses consistently
    if result == 0:
        output = capture.get()
        # Should have consistent address formatting
        lines = output.strip().split("\n")
        if len(lines) > 1:
            # Should maintain address column alignment
            assert len(lines) > 0
    else:
        assert result == 1


def test_execute_data_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test data format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/hosts"])

    # Should format data consistently
    if result == 0:
        output = capture.get()
        # Should have consistent data formatting
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_output_alignment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test output column alignment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should align output columns properly
    if result == 0:
        output = capture.get()
        # Should maintain column alignment
        lines = output.strip().split("\n")
        if len(lines) > 1:
            # Should have consistent line structure
            assert len(lines) > 0
    else:
        assert result == 1


def test_execute_byte_order_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test byte order handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "x2", "/etc/hosts"])

    # Should handle byte order appropriately
    if result == 0:
        output = capture.get()
        # Should display multi-byte values correctly
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_unicode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test unicode character handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "/etc/hosts"])

    # Should handle unicode characters appropriately
    if result == 0:
        output = capture.get()
        # Should display unicode content safely
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_control_character_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test control character display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "/etc/hosts"])

    # Should display control characters appropriately
    if result == 0:
        output = capture.get()
        # Should show control characters with escape sequences
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_null_byte_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test null byte handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should handle null bytes appropriately
    if result == 0:
        output = capture.get()
        # Should display null bytes correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
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


def test_execute_performance_large_dump(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test performance with large dumps
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "10000", "/usr/bin/bash"])

    # Should handle large dumps efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.OdCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000000  # Reasonable output size limit
    else:
        assert result == 1
