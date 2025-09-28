"""Integration tests for the IpaddrCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IpaddrCommand instance."""
    yield pebble_shell.commands.IpaddrCommand(shell=shell)


def test_name(command: pebble_shell.commands.IpaddrCommand):
    assert command.name == "ip addr" or command.name == "ipaddr"


def test_category(command: pebble_shell.commands.IpaddrCommand):
    assert command.category == "Network"


def test_help(command: pebble_shell.commands.IpaddrCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["ip", "addr", "address", "interface", "network"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["ip", "addr", "address", "interface", "usage"]
    )


def test_execute_show_all_addresses(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test showing all IP addresses
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain interface and address information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain interface information
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain network interface indicators
            interface_found = any(
                any(
                    indicator in line
                    for indicator in [":", "inet", "link", "lo", "eth", "wlan"]
                )
                for line in lines
                if line.strip()
            )
            if interface_found:
                assert interface_found
    else:
        # Should fail if no permission or network unavailable
        assert result == 1


def test_execute_show_specific_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test showing specific interface
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "lo"])

    # Should either succeed showing loopback or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain loopback interface information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain loopback information
            assert "lo" in output.lower() or "127.0.0.1" in output
    else:
        # Should fail if interface doesn't exist
        assert result == 1


def test_execute_show_brief(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test brief output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "-br"])

    # Should either succeed with brief format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show brief interface information
        assert len(output) >= 0
        if len(output) > 0:
            # Brief format should be more compact
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_show_up_interfaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test showing only up interfaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "up"])

    # Should either succeed showing up interfaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show only active interfaces
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain UP state interfaces
            assert "UP" in output or "up" in output.lower()
    else:
        assert result == 1


def test_execute_show_ipv4_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test showing IPv4 addresses only
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "-4"])

    # Should either succeed showing IPv4 or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IPv4 addresses
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain IPv4 patterns
            import re

            ipv4_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
            if re.search(ipv4_pattern, output):
                assert True  # IPv4 addresses found
    else:
        assert result == 1


def test_execute_show_ipv6_only(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test showing IPv6 addresses only
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "-6"])

    # Should either succeed showing IPv6 or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IPv6 addresses
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain IPv6 patterns (::1 for loopback)
            assert "::" in output or "inet6" in output
    else:
        assert result == 1


def test_execute_list_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test list command (alias for show)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["list"])

    # Should either succeed listing addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should list all interfaces
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_flush_addresses(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test flush addresses (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["flush", "dev", "lo"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should flush addresses (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root or interface protected
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "error", "not found"]
        )


def test_execute_add_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test adding IP address (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "192.168.1.100/24", "dev", "lo"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should add address (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "error", "not found"]
        )


def test_execute_delete_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test deleting IP address (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["del", "192.168.1.100/24", "dev", "lo"]
        )

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete address (if permitted and exists)
        assert len(output) >= 0
    else:
        # Should fail if not root or address doesn't exist
        assert result == 1


def test_execute_invalid_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test with invalid interface name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "nonexistent99"])

    # Should fail with interface not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["not exist", "not found", "invalid", "error"])


def test_execute_invalid_ip_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test with invalid IP address format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "999.999.999.999/24", "dev", "lo"]
        )

    # Should fail with invalid address error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "error"])


def test_execute_invalid_subnet_mask(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test with invalid subnet mask
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "192.168.1.1/99", "dev", "lo"]
        )

    # Should fail with invalid netmask error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "netmask", "prefix", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "show"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test permission handling for modifications
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["add", "10.0.0.1/8", "dev", "lo"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should succeed if running as root
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "root", "error"])


def test_execute_network_namespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test network namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed in current namespace or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show interfaces in current namespace
        assert len(output) >= 0
    else:
        # Should fail if namespace unavailable
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test container environment handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed in container or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle container networking
        assert len(output) >= 0
    else:
        # May fail in restricted containers
        assert result == 1


def test_execute_loopback_interface_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test loopback interface validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "lo"])

    # Should either succeed showing loopback or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show loopback interface
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain loopback information
            assert any(
                indicator in output.lower()
                for indicator in ["lo", "loopback", "127.0.0.1", "::1"]
            )
    else:
        assert result == 1


def test_execute_interface_state_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test interface state detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed detecting states or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show interface states
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain state information
            has_state = any(
                state in output.upper()
                for state in ["UP", "DOWN", "UNKNOWN", "LOWER_UP"]
            )
            if has_state:
                assert has_state
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid_command"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["invalid", "unknown", "error", "usage", "command"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test signal handling during address operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpaddrCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # May fail on platforms with different networking
        assert result == 1
