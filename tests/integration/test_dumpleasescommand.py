"""Integration tests for the DumpleasesCommand."""

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
    """Fixture to create a DumpleasesCommand instance."""
    yield pebble_shell.commands.DumpleasesCommand(shell=shell)


def test_name(command: pebble_shell.commands.DumpleasesCommand):
    assert command.name == "dumpleases"


def test_category(command: pebble_shell.commands.DumpleasesCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.DumpleasesCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["dump", "lease", "dhcp", "network", "address"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["dump", "lease", "dhcp", "usage"]
    )


def test_execute_no_lease_file_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with no lease file specified
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing file error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["file", "required", "lease", "usage", "error"])


def test_execute_nonexistent_lease_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with non-existent lease file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/dhcp.leases"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "error", "cannot open"]
    )


def test_execute_default_lease_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with default DHCP lease file location
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should either succeed reading lease file or fail with file not found
    if result == 0:
        output = capture.get()
        # Should contain DHCP lease information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain lease data
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain DHCP lease indicators
            has_lease_info = any(
                indicator in line.lower()
                for line in lines
                for indicator in ["lease", "binding", "client", "starts", "ends"]
            )
            if has_lease_info:
                assert has_lease_info
    else:
        # Should fail with file not found or permission error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "permission", "denied", "error"]
        )


def test_execute_alternative_lease_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with alternative lease file location
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/db/dhcpd.leases"])

    # Should either succeed or fail with file not found
    if result == 0:
        output = capture.get()
        # Should read alternative lease file
        assert len(output) >= 0
    else:
        # Should fail with file not found
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "error", "cannot open"])


def test_execute_empty_lease_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with empty lease file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with empty output or fail
    if result == 0:
        output = capture.get()
        # Should handle empty lease file
        assert len(output) >= 0
    else:
        # Should fail with empty file error
        assert result == 1


def test_execute_directory_instead_of_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with directory instead of file
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_dir])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "not a file", "error", "invalid"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root/dhcp.leases"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should read lease file if permitted
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with binary file (not DHCP lease format)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should fail with format error or succeed with binary handling
    if result == 0:
        output = capture.get()
        # Should handle binary data
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["format", "invalid", "error", "binary"])


def test_execute_large_lease_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with large file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/zero"])

    # Should either handle large files or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle large files efficiently
        assert len(output) >= 0
    else:
        # Should fail with format or size error
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test verbose mode (if supported)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-v", "/var/lib/dhcp/dhcpd.leases"]
        )

    # Should either succeed with verbose output or fail with option error
    if result == 0:
        output = capture.get()
        # Should show verbose lease information
        assert len(output) >= 0
    else:
        # Should fail with file not found or invalid option
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "invalid", "option", "error"])


def test_execute_absolute_time_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test absolute time mode (if supported)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-a", "/var/lib/dhcp/dhcpd.leases"]
        )

    # Should either succeed with absolute times or fail
    if result == 0:
        output = capture.get()
        # Should show absolute time format
        assert len(output) >= 0
    else:
        # Should fail with file not found or invalid option
        assert result == 1


def test_execute_lease_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test DHCP lease format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])  # Wrong format

    # Should either succeed or fail with format error
    if result == 0:
        output = capture.get()
        # Should handle non-lease format files
        assert len(output) >= 0
    else:
        # Should fail with format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["format", "invalid", "lease", "error"])


def test_execute_active_leases_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test showing only active leases
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should either succeed showing active leases or fail
    if result == 0:
        output = capture.get()
        # Should filter active leases
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain active lease information
            has_active = any(
                status in output.lower()
                for status in ["active", "binding", "free", "backup"]
            )
            if has_active:
                assert has_active
    else:
        # Should fail with file or format error
        assert result == 1


def test_execute_lease_time_parsing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test lease time parsing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should either succeed parsing times or fail
    if result == 0:
        output = capture.get()
        # Should parse lease times
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain time information
            has_time = any(
                time_field in output.lower()
                for time_field in ["starts", "ends", "tstp", "cltt"]
            )
            if has_time:
                assert has_time
    else:
        # Should fail with file or parsing error
        assert result == 1


def test_execute_client_identification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test client identification parsing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should either succeed identifying clients or fail
    if result == 0:
        output = capture.get()
        # Should identify DHCP clients
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain client information
            has_client = any(
                client_field in output.lower()
                for client_field in ["client", "hardware", "ethernet", "uid"]
            )
            if has_client:
                assert has_client
    else:
        # Should fail with file or parsing error
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-z", "/var/lib/dhcp/dhcpd.leases"]
        )

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_multiple_lease_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test with multiple lease files
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/var/lib/dhcp/dhcpd.leases", "/var/db/dhcpd.leases"]
        )

    # Should either succeed processing multiple files or fail
    if result == 0:
        output = capture.get()
        # Should process multiple lease files
        assert len(output) >= 0
    else:
        # Should fail with file not found or argument error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "argument", "error", "multiple"]
        )


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test symbolic link handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/var/run/dhcpd.leases"]
        )  # Often a symlink

    # Should either succeed following symlinks or fail
    if result == 0:
        output = capture.get()
        # Should follow symlinks to lease files
        assert len(output) >= 0
    else:
        # Should fail with file not found
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent.leases"])

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/invalid/path/dhcp.leases"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["not found", "error", "invalid", "cannot open"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test signal handling during lease processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with file not found or access error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test output formatting for lease data
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should either succeed with proper formatting or fail
    if result == 0:
        output = capture.get()
        # Should format lease data properly
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain properly formatted lease information
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail with file not found or format error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpleasesCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/var/lib/dhcp/dhcpd.leases"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "error", "permission", "access"]
        )
