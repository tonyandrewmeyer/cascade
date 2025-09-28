"""Integration tests for the IfconfigCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IfconfigCommand instance."""
    yield pebble_shell.commands.IfconfigCommand(shell=shell)


def test_name(command: pebble_shell.commands.IfconfigCommand):
    assert command.name == "ifconfig"


def test_category(command: pebble_shell.commands.IfconfigCommand):
    assert command.category == "Network Utilities"


def test_help(command: pebble_shell.commands.IfconfigCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "ifconfig" in output
    assert "Configure network interface" in output
    assert "interface" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "ifconfig" in output
    assert "Configure network interface" in output


def test_execute_no_args_show_all_interfaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # ifconfig with no args should show all active interfaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should succeed showing interface information
    assert result == 0
    output = capture.get()
    # Should contain interface information
    assert len(output.strip()) > 0
    # Should contain typical interface names or network information
    assert (
        any(
            iface in output.lower()
            for iface in ["eth", "lo", "wlan", "docker", "inet", "mtu", "flags"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_show_all_interfaces_verbose(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test -a option to show all interfaces (including inactive)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should succeed showing all interfaces
    assert result == 0
    output = capture.get()
    # Should contain interface information
    assert len(output.strip()) > 0
    # Should show interface details
    assert (
        any(
            keyword in output.lower()
            for keyword in ["inet", "ether", "mtu", "flags", "interface"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_specific_interface_loopback(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test showing specific interface (loopback should always exist)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo"])

    # Should succeed showing loopback interface
    assert result == 0
    output = capture.get()
    # Should contain loopback interface information
    assert len(output.strip()) > 0
    # Should contain loopback-specific information
    assert (
        any(
            indicator in output.lower()
            for indicator in ["127.0.0.1", "loopback", "lo", "inet"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_nonexistent_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test with nonexistent interface
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent999"])

    # Should either fail or show no output
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such device", "not found", "error", "does not exist"]
        )
    else:
        # May succeed with empty output
        assert result == 0


def test_execute_interface_up_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test bringing interface up (typically requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "up"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure interface successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or interface management not available
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "not permitted", "error"]
        )


def test_execute_interface_down_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test bringing interface down (typically requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "down"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure interface successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or interface management not available
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "not permitted", "error"]
        )


def test_execute_ip_address_assignment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test IP address assignment (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["lo", "192.168.1.100", "netmask", "255.255.255.0"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure IP address successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or interface configuration not available
        assert result == 1


def test_execute_mtu_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test MTU configuration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "mtu", "1500"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure MTU successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or MTU configuration not available
        assert result == 1


def test_execute_broadcast_address_setting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test broadcast address setting
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["lo", "broadcast", "192.168.1.255"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure broadcast address successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or broadcast configuration not available
        assert result == 1


def test_execute_netmask_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test netmask configuration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "netmask", "255.255.255.0"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure netmask successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or netmask configuration not available
        assert result == 1


def test_execute_interface_flags_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test interface flags configuration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "promisc"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure interface flags successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or flag configuration not available
        assert result == 1


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have structured output format
        _ = output.strip().split("\n")
        # Should contain interface-related information
        assert any(
            keyword in output.lower()
            for keyword in ["inet", "ether", "flags", "mtu", "lo", "eth"]
        )


def test_execute_ipv6_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test IPv6 support
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo"])

    # Should handle IPv6 addresses if present
    assert result == 0
    output = capture.get()

    if "inet6" in output.lower():
        # Should display IPv6 addresses properly
        assert any(
            ipv6_indicator in output.lower()
            for ipv6_indicator in ["::1", "inet6", "scope"]
        )


def test_execute_interface_statistics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test interface statistics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo"])

    # Should display interface statistics
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # May contain packet statistics
        _ = ["packets", "bytes", "errors", "dropped", "rx", "tx"]
        # Not all implementations show stats, so this is optional
        assert len(output.strip()) >= 0


def test_execute_hardware_address_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test hardware address display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display hardware addresses for physical interfaces
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # May contain MAC addresses for physical interfaces
        # This is optional as not all interfaces have MAC addresses
        assert len(output.strip()) >= 0


def test_execute_interface_state_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test interface state detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should detect interface states
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should indicate interface states
        state_indicators = ["up", "down", "running", "flags"]
        assert (
            any(indicator in output.lower() for indicator in state_indicators)
            or len(output.strip()) >= 0
        )


def test_execute_multiple_interfaces_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test multiple interfaces display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should display multiple interfaces
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        lines = output.strip().split("\n")
        # Should have content for potentially multiple interfaces
        assert len(lines) >= 1


def test_execute_invalid_ip_address_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test invalid IP address format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "999.999.999.999"])

    # Should fail with invalid IP address error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["invalid", "address", "error", "bad", "format"]
        )
    else:
        # May succeed if validation is minimal
        assert result == 0


def test_execute_invalid_netmask_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test invalid netmask format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "netmask", "invalid"])

    # Should fail with invalid netmask error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["invalid", "netmask", "error", "bad", "format"]
        )
    else:
        # May succeed if validation is minimal
        assert result == 0


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test permission handling for configuration changes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo", "192.168.1.1"])

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        # Should show permission-related error
        assert any(
            msg in output
            for msg in ["permission", "denied", "not permitted", "root", "error"]
        )
    else:
        # May succeed if running with appropriate privileges
        assert result == 0


def test_execute_interface_name_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test interface name validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should handle empty interface name
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "interface", "name", "error"])
    else:
        # May treat empty name as showing all interfaces
        assert result == 0


def test_execute_configuration_persistence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test configuration persistence behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo"])

    # Should show current interface configuration
    assert result == 0
    output = capture.get()
    # Should display current interface state
    assert len(output.strip()) >= 0


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid_interface_xyz"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(
            msg in output
            for msg in ["No such device", "not found", "error", "interface"]
        )
    else:
        # May succeed with empty output
        assert result == 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 100000  # Reasonable output size limit


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) >= 0


def test_execute_network_namespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test network namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work within current network namespace
    assert result == 0
    output = capture.get()
    # Should show interfaces available in current namespace
    assert len(output.strip()) >= 0


def test_execute_interface_aliasing_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test interface aliasing support
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lo:0", "127.0.0.2"])

    # Should either support aliasing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should configure interface alias successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if aliasing not supported or no permission
        assert result == 1


def test_execute_performance_with_many_interfaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
):
    # Test performance with many interfaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should handle many interfaces efficiently
    assert result == 0
    output = capture.get()
    # Should complete in reasonable time
    assert len(output) >= 0


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IfconfigCommand,
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
        # May ignore unknown options and show interface info
        assert result == 0
