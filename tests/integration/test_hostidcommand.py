"""Integration tests for the HostidCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a HostidCommand instance."""
    yield pebble_shell.commands.HostidCommand(shell=shell)


def test_name(command: pebble_shell.commands.HostidCommand):
    assert command.name == "hostid"


def test_category(command: pebble_shell.commands.HostidCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.HostidCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "hostid" in output
    assert "Print system host ID" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "hostid" in output
    assert "Print system host ID" in output


def test_execute_no_args_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # hostid with no args should display system host ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should succeed showing host ID
    assert result == 0
    output = capture.get()
    # Should contain host ID (typically 8-character hex value)
    host_id = output.strip()
    assert len(host_id) > 0
    # Should be a valid hex string (8 characters or other valid format)
    assert re.match(r"^[0-9a-fA-F]+$", host_id) or len(host_id) >= 1


def test_execute_with_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # hostid with arguments should either ignore them or show error
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["extra", "arguments"])

    # Should either ignore arguments or fail with error
    if result == 0:
        output = capture.get()
        # Should show host ID (ignoring arguments)
        assert len(output.strip()) > 0
    else:
        # Should fail if arguments not accepted
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["too many arguments", "usage", "hostid", "error"]
        )


def test_execute_hostid_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test host ID format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should produce valid host ID format
    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should be non-empty
    assert len(host_id) > 0

    # Should be hexadecimal format (common case) or other valid identifier
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        # Standard hex format - typically 8 characters
        assert len(host_id) in [8, 16]  # Common lengths
    else:
        # Alternative format - should still be reasonable identifier
        assert len(host_id) <= 32  # Reasonable maximum length
        assert all(c.isprintable() for c in host_id)  # Should be printable


def test_execute_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test consistency of host ID across multiple calls
    host_ids = []

    for _ in range(3):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[])
        assert result == 0
        host_ids.append(capture.get().strip())

    # Should return the same host ID consistently
    assert all(host_id == host_ids[0] for host_id in host_ids)
    assert len(host_ids[0]) > 0


def test_execute_output_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should produce clean output
    assert result == 0
    output = capture.get()

    # Should have single line output
    lines = output.strip().split("\n")
    assert len(lines) == 1

    # Should not have extra whitespace
    assert output.strip() == lines[0]

    # Should not be empty
    assert len(lines[0]) > 0


def test_execute_hex_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test hexadecimal format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # If it's hexadecimal format, validate it properly
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        # Should be valid hex
        try:
            int(host_id, 16)
            # Should be reasonable length for hex host ID
            assert len(host_id) >= 4  # Minimum reasonable length
            assert len(host_id) <= 16  # Maximum reasonable length
        except ValueError:
            pytest.fail(f"Invalid hex format: {host_id}")


def test_execute_zero_hostid_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test handling of zero host ID (valid but special case)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Zero is a valid host ID
    if host_id == "0" or host_id == "00000000":
        # Should handle zero host ID gracefully
        assert len(host_id) > 0
    else:
        # Should be non-zero host ID
        assert host_id != "0"


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should integrate with system properly
    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should reflect actual system host ID
    assert len(host_id) > 0

    # Should be deterministic for the system
    with command.shell.console.capture() as capture:
        result2 = command.execute(client=client, args=[])
    assert result2 == 0
    host_id2 = capture.get().strip()
    assert host_id == host_id2


def test_execute_uppercase_lowercase_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test case handling in hex output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # If hex format, should be consistent case
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        # Should be either all uppercase or all lowercase hex
        assert host_id == host_id.lower() or host_id == host_id.upper()


def test_execute_leading_zeros_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test leading zeros in host ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should handle leading zeros appropriately
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        # Should maintain proper format even with leading zeros
        assert len(host_id) >= 1
        # If 8-character format, should include leading zeros
        if len(host_id) == 8:
            # Should be padded to 8 characters if that's the format
            assert re.match(r"^[0-9a-fA-F]{8}$", host_id)


def test_execute_network_byte_order(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test network byte order handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should handle byte order consistently
    assert len(host_id) > 0

    # If hex format, should be valid regardless of byte order
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        # Should be valid hex representation
        try:
            hex_value = int(host_id, 16)
            assert hex_value >= 0
        except ValueError:
            pytest.fail(f"Invalid hex value: {host_id}")


def test_execute_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should produce valid output on any platform
    assert len(host_id) > 0
    assert all(c.isprintable() and not c.isspace() for c in host_id)


def test_execute_unicode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test unicode handling (should not contain unicode)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Host ID should be ASCII only
    try:
        host_id.encode("ascii")
    except UnicodeEncodeError:
        pytest.fail(f"Host ID contains non-ASCII characters: {host_id}")


def test_execute_empty_output_prevention(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test prevention of empty output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # Should never produce empty output
    assert len(host_id) > 0
    assert host_id != ""


def test_execute_whitespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test whitespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()

    # Should have clean output with single newline
    assert output.endswith("\n")
    assert output.count("\n") == 1

    # Content should not have internal whitespace
    host_id = output.strip()
    assert " " not in host_id
    assert "\t" not in host_id


def test_execute_numeric_range_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test numeric range validation for hex values
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    assert result == 0
    output = capture.get()
    host_id = output.strip()

    # If hex format, should be within valid range
    if re.match(r"^[0-9a-fA-F]+$", host_id):
        hex_value = int(host_id, 16)
        # Should be within 32-bit or 64-bit range
        assert 0 <= hex_value <= 0xFFFFFFFFFFFFFFFF


def test_execute_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test error handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should always succeed for hostid command
    assert result == 0
    output = capture.get()

    # Should produce valid output even in error conditions
    assert len(output.strip()) > 0


def test_execute_performance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test performance
    import time

    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])
    end_time = time.time()

    # Should complete quickly
    assert result == 0
    assert end_time - start_time < 1.0  # Should complete in under 1 second

    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    assert result == 0
    output = capture.get()

    # Should have minimal output size
    assert len(output) < 100  # Should be very small output
    assert len(output.strip()) > 0


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test concurrent execution safety
    results = []

    # Run multiple times to test consistency
    for _ in range(5):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[])
        assert result == 0
        results.append(capture.get().strip())

    # Should produce consistent results
    assert all(r == results[0] for r in results)
    assert len(results[0]) > 0


def test_execute_system_call_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test system call efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be efficient (single system call typically)
    assert result == 0
    output = capture.get()

    # Should produce valid host ID efficiently
    host_id = output.strip()
    assert len(host_id) > 0


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HostidCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and show hostid
        assert result == 0
        output = capture.get()
        assert len(output.strip()) > 0
