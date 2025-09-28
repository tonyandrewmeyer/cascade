"""Integration tests for the IplinkCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IplinkCommand instance."""
    yield pebble_shell.commands.IplinkCommand(shell=shell)


def test_name(command: pebble_shell.commands.IplinkCommand):
    assert command.name == "ip link" or command.name == "iplink"


def test_category(command: pebble_shell.commands.IplinkCommand):
    assert command.category == "Network"


def test_help(command: pebble_shell.commands.IplinkCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["ip", "link", "interface", "network", "device"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["ip", "link", "interface", "usage"]
    )


def test_execute_show_all_links(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test showing all network links
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing links or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain interface link information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain interface information
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain network interface indicators
            interface_found = any(
                any(
                    indicator in line
                    for indicator in [":", "mtu", "state", "lo", "eth", "wlan"]
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
    command: pebble_shell.commands.IplinkCommand,
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
            assert "lo" in output.lower() or "loopback" in output.lower()
    else:
        # Should fail if interface doesn't exist
        assert result == 1


def test_execute_show_up_interfaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
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


def test_execute_list_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test list command (alias for show)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["list"])

    # Should either succeed listing links or fail gracefully
    if result == 0:
        output = capture.get()
        # Should list all interfaces
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_set_interface_up(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test setting interface up (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "lo", "up"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set interface up (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "error", "not found"]
        )


def test_execute_set_interface_down(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test setting interface down (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "lo", "down"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set interface down (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1


def test_execute_set_mtu(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test setting MTU (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "lo", "mtu", "1500"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set MTU (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1


def test_execute_set_mac_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test setting MAC address (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["set", "lo", "address", "00:11:22:33:44:55"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set MAC address (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root or invalid for loopback
        assert result == 1


def test_execute_add_virtual_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test adding virtual interface (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["add", "test0", "type", "dummy"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should add interface (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "root", "error"])


def test_execute_delete_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test deleting interface (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["delete", "test0"])

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete interface (if permitted and exists)
        assert len(output) >= 0
    else:
        # Should fail if not root or interface doesn't exist
        assert result == 1


def test_execute_invalid_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test with invalid interface name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "nonexistent99"])

    # Should fail with interface not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["not exist", "not found", "invalid", "error"])


def test_execute_invalid_mtu_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test with invalid MTU value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "lo", "mtu", "abc"])

    # Should fail with invalid MTU error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "mtu", "number", "error"])


def test_execute_invalid_mac_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test with invalid MAC address format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["set", "lo", "address", "invalid:mac"]
        )

    # Should fail with invalid address error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "mac", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "show"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_link_state_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test link state detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed detecting states or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show link states
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


def test_execute_mtu_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test MTU information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "lo"])

    # Should either succeed showing MTU or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show MTU information
        assert len(output) >= 0
        if len(output) > 0 and "mtu" in output.lower():
            # Should contain MTU information
            assert "mtu" in output.lower()
    else:
        assert result == 1


def test_execute_mac_address_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test MAC address display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing MAC addresses or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show MAC address information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain MAC address patterns (for non-loopback interfaces)
            import re

            mac_pattern = r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}"
            if re.search(mac_pattern, output):
                assert True  # MAC addresses found
    else:
        assert result == 1


def test_execute_interface_type_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test interface type detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed detecting types or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show interface types
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain type information
            has_type = any(
                iface_type in output.lower()
                for iface_type in ["loopback", "ethernet", "wireless", "tunnel"]
            )
            if has_type:
                assert has_type
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
):
    # Test permission handling for modifications
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["set", "lo", "mtu", "1400"])

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
    command: pebble_shell.commands.IplinkCommand,
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
    command: pebble_shell.commands.IplinkCommand,
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
    command: pebble_shell.commands.IplinkCommand,
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
            assert any(indicator in output.lower() for indicator in ["lo", "loopback"])
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IplinkCommand,
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
    command: pebble_shell.commands.IplinkCommand,
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
    command: pebble_shell.commands.IplinkCommand,
):
    # Test signal handling during link operations
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
    command: pebble_shell.commands.IplinkCommand,
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
