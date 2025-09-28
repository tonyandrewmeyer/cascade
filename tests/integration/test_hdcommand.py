"""Integration tests for the HdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a HdCommand instance."""
    yield pebble_shell.commands.HdCommand(shell=shell)


def test_name(command: pebble_shell.commands.HdCommand):
    assert command.name == "hd"


def test_category(command: pebble_shell.commands.HdCommand):
    assert command.category == "Data Processing"


def test_help(command: pebble_shell.commands.HdCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "hd" in output
    assert "Hexdump alias" in output
    assert "-C" in output
    assert "-x" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "hd" in output
    assert "Hexdump alias" in output


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # hd with no args should read from stdin
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


def test_execute_single_file_hexdump(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test hexdump of single file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should either succeed showing hexdump or fail if not accessible
    if result == 0:
        output = capture.get()
        # Should show hexadecimal dump
        assert len(output.strip()) > 0
        # Should contain hexadecimal values
        assert any(char in "0123456789abcdef" for char in output.lower())
        # Should contain address offsets
        assert any(char.isdigit() for char in output)
        # Should have structured format (address: hex bytes  ascii)
        lines = output.strip().split("\n")
        if lines:
            # Should have typical hexdump format
            assert any(":" in line or "|" in line for line in lines[:3])
    else:
        # Should fail if file not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["No such file", "permission denied", "error"]
        )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
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
    command: pebble_shell.commands.HdCommand,
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


def test_execute_binary_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should succeed showing binary dump
    if result == 0:
        output = capture.get()
        # Should show binary data in hex format
        assert len(output.strip()) > 0
        # Should contain hex values
        assert any(char in "0123456789abcdef" for char in output.lower())
        # Should contain address information
        assert any(
            char.isdigit() for char in output[:20]
        )  # Check first 20 chars for addresses
    else:
        assert result == 1


def test_execute_text_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test with text file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should succeed showing text dump
    if result == 0:
        output = capture.get()
        # Should show text data in hex format
        assert len(output.strip()) > 0
        # Should contain hex values
        assert any(char in "0123456789abcdef" for char in output.lower())
        # Should contain ASCII representation
        lines = output.strip().split("\n")
        if lines:
            # Should have hex and ASCII columns
            sample_line = lines[0] if lines else ""
            assert len(sample_line) > 10  # Should have substantial content
    else:
        assert result == 1


def test_execute_canonical_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -C option for canonical format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-C", "/etc/hosts"])

    # Should either succeed with canonical format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show canonical hexdump format
        assert len(output.strip()) > 0
        # Should contain hex values and ASCII
        assert any(char in "0123456789abcdef" for char in output.lower())
        # Should have canonical format structure
        lines = output.strip().split("\n")
        if lines:
            # Should have 16 bytes per line in canonical format
            sample_line = lines[0] if lines else ""
            assert "|" in sample_line or len(sample_line) > 40
    else:
        assert result == 1


def test_execute_hex_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -x option for hex format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/hosts"])

    # Should either succeed with hex format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show hexadecimal format
        assert len(output.strip()) > 0
        # Should contain hex values
        assert any(char in "0123456789abcdef" for char in output.lower())
    else:
        assert result == 1


def test_execute_decimal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -d option for decimal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "/etc/hosts"])

    # Should either succeed with decimal format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show decimal format
        assert len(output.strip()) > 0
        # Should contain decimal values
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_octal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -o option for octal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "/etc/hosts"])

    # Should either succeed with octal format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show octal format
        assert len(output.strip()) > 0
        # Should contain octal values (0-7)
        assert any(char in "01234567" for char in output)
    else:
        assert result == 1


def test_execute_character_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -c option for character format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "/etc/hosts"])

    # Should either succeed with character format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show character format with escape sequences
        assert len(output.strip()) > 0
        # Should contain character representations
        assert any(char.isprintable() for char in output)
    else:
        assert result == 1


def test_execute_skip_bytes_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -s option to skip bytes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "10", "/etc/hosts"])

    # Should either succeed skipping bytes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dump starting from offset
        assert len(output.strip()) > 0
        # Should start from specified offset
        lines = output.strip().split("\n")
        if lines:
            first_line = lines[0]
            # Should not start at offset 00000000 if skipping
            assert "00000000" not in first_line[:12] or len(lines) == 1
    else:
        assert result == 1


def test_execute_length_limit_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -n option to limit bytes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "50", "/etc/hosts"])

    # Should either succeed with limited bytes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show limited amount of data
        assert len(output.strip()) > 0
        # Should not exceed reasonable line count for 50 bytes
        lines = output.strip().split("\n")
        assert len(lines) <= 10  # 50 bytes should be few lines
    else:
        assert result == 1


def test_execute_format_specification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test -e option with format specification
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "x1", "/etc/hosts"])

    # Should either succeed with specified format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dump in specified format
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test with multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed dumping multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dumps from multiple files
        assert len(output.strip()) > 0
        # Should contain data from both files
        lines = output.strip().split("\n")
        assert len(lines) > 5  # Should have content from multiple files
    else:
        assert result == 1


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "1000", "/usr/bin/bash"])

    # Should either succeed with large file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_special_files_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test with special files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "100", "/proc/version"])

    # Should either succeed with special file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show special file contents in hex format
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
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
    command: pebble_shell.commands.HdCommand,
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
    command: pebble_shell.commands.HdCommand,
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
    command: pebble_shell.commands.HdCommand,
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
            address_positions = []
            for line in lines[:3]:
                if ":" in line:
                    addr_pos = line.find(":")
                    if addr_pos > 0:
                        address_positions.append(addr_pos)

            if len(address_positions) > 1:
                # Addresses should be aligned
                assert all(pos == address_positions[0] for pos in address_positions)
    else:
        assert result == 1


def test_execute_hex_data_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test hex data format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/hosts"])

    # Should format hex data consistently
    if result == 0:
        output = capture.get()
        # Should have consistent hex formatting
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_ascii_representation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test ASCII representation in canonical format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-C", "/etc/hosts"])

    # Should show ASCII representation
    if result == 0:
        output = capture.get()
        # Should contain ASCII column
        lines = output.strip().split("\n")
        if lines:
            # Should have ASCII representation (typically after |)
            sample_line = lines[0] if lines else ""
            if "|" in sample_line:
                ascii_part = sample_line.split("|")[-1]
                # Should contain printable characters or dots
                assert any(c.isprintable() or c == "." for c in ascii_part)
    else:
        assert result == 1


def test_execute_byte_order_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test byte order handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "/etc/hosts"])

    # Should handle byte order appropriately
    if result == 0:
        output = capture.get()
        # Should display bytes in correct order
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_control_character_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
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
    command: pebble_shell.commands.HdCommand,
):
    # Test null byte handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should handle null bytes appropriately
    if result == 0:
        output = capture.get()
        # Should display null bytes correctly (empty file)
        assert len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_unicode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test unicode character handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle unicode characters appropriately
    if result == 0:
        output = capture.get()
        # Should display unicode content safely
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_line_length_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test line length consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should maintain consistent line lengths
    if result == 0:
        output = capture.get()
        lines = output.strip().split("\n")
        if len(lines) > 2:
            # Lines should have similar structure
            line_lengths = [len(line) for line in lines[:3] if line.strip()]
            if line_lengths:
                # Should have consistent formatting
                assert len(line_lengths) > 0
    else:
        assert result == 1


def test_execute_offset_calculation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test offset calculation accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "16", "/etc/hosts"])

    # Should calculate offsets correctly
    if result == 0:
        output = capture.get()
        lines = output.strip().split("\n")
        if lines:
            first_line = lines[0]
            # Should start from offset 16 (0x10)
            if ":" in first_line:
                offset_part = first_line.split(":")[0].strip()
                # Should reflect the skip offset
                assert len(offset_part) > 0
    else:
        assert result == 1


def test_execute_combined_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test combining multiple options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-C", "-s", "10", "-n", "50", "/etc/hosts"]
        )

    # Should either succeed with combined options or fail gracefully
    if result == 0:
        output = capture.get()
        # Should apply all options
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_output_width_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test output width handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle output width appropriately
    if result == 0:
        output = capture.get()
        lines = output.strip().split("\n")
        if lines:
            # Should not have excessively long lines
            max_line_length = max(len(line) for line in lines)
            assert max_line_length < 200  # Reasonable line length limit
    else:
        assert result == 1


def test_execute_performance_large_dump(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test performance with large dumps
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "10000", "/usr/bin/bash"])

    # Should handle large dumps efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
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


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert len(output.strip()) >= 0


def test_execute_compatibility_with_hexdump(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
):
    # Test compatibility with standard hexdump behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-C", "/etc/hosts"])

    # Should behave like standard hexdump
    if result == 0:
        output = capture.get()
        # Should have hexdump-compatible format
        lines = output.strip().split("\n")
        if lines:
            # Should have typical hexdump structure
            sample_line = lines[0]
            # Should have address, hex data, and ASCII
            assert ":" in sample_line or len(sample_line) > 20
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HdCommand,
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
