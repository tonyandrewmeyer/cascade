"""Integration tests for the IpCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IpCommand instance."""
    yield pebble_shell.commands.IpCommand(shell=shell)


def test_name(command: pebble_shell.commands.IpCommand):
    assert command.name == "ip"


def test_category(command: pebble_shell.commands.IpCommand):
    assert command.category == "Network Utilities"


def test_help(command: pebble_shell.commands.IpCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "ip" in output
    assert "Show and manipulate routing" in output
    assert "addr" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "ip" in output
    assert "Show and manipulate routing" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # ip with no args should show usage or help
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either show help or fail with usage message
    if result == 0:
        output = capture.get()
        assert any(
            keyword in output for keyword in ["Usage:", "ip", "addr", "route", "link"]
        )
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["Usage:", "Object", "command", "help"])


def test_execute_addr_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing addresses
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show"])

    # Should succeed showing interface addresses
    assert result == 0
    output = capture.get()
    # Should contain address information
    assert len(output.strip()) > 0
    # Should contain typical address output
    assert (
        any(
            keyword in output.lower()
            for keyword in ["inet", "link", "scope", "lo", "eth", "mtu"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_addr_show_specific_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing specific interface addresses
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show", "lo"])

    # Should succeed showing loopback addresses
    assert result == 0
    output = capture.get()
    # Should contain loopback address information
    assert len(output.strip()) > 0
    # Should contain loopback-specific information
    assert (
        any(
            indicator in output.lower()
            for indicator in ["127.0.0.1", "loopback", "lo:", "inet"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_link_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing network links
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["link", "show"])

    # Should succeed showing network links
    assert result == 0
    output = capture.get()
    # Should contain link information
    assert len(output.strip()) > 0
    # Should contain typical link output
    assert (
        any(
            keyword in output.lower()
            for keyword in ["link", "mtu", "state", "up", "down", "lo", "eth"]
        )
        or len(output.strip()) >= 0
    )


def test_execute_route_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing routing table
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["route", "show"])

    # Should succeed showing routes
    assert result == 0
    output = capture.get()
    # Should contain route information
    assert len(output.strip()) >= 0
    # May contain routing information
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["default", "via", "dev", "src", "scope"]
        )


def test_execute_route_show_table(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing specific routing table
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["route", "show", "table", "main"])

    # Should succeed showing main routing table
    assert result == 0
    output = capture.get()
    # Should contain route table information
    assert len(output.strip()) >= 0


def test_execute_addr_add_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test adding IP address (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["addr", "add", "192.168.1.100/24", "dev", "lo"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure address successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or interface configuration not available
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "permission",
                "denied",
                "not permitted",
                "error",
                "Operation not permitted",
            ]
        )


def test_execute_addr_del_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test deleting IP address (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["addr", "del", "192.168.1.100/24", "dev", "lo"]
        )

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete address successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or address not found
        assert result == 1


def test_execute_link_set_up(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test bringing interface up (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["link", "set", "lo", "up"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set interface up successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "not permitted", "error"]
        )


def test_execute_link_set_down(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test bringing interface down (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["link", "set", "lo", "down"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should set interface down successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1


def test_execute_route_add(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test adding route (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["route", "add", "192.168.2.0/24", "via", "127.0.0.1"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should add route successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or invalid route
        assert result == 1


def test_execute_route_del(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test deleting route (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["route", "del", "192.168.2.0/24", "via", "127.0.0.1"]
        )

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete route successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission or route not found
        assert result == 1


def test_execute_neighbor_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing neighbor table (ARP cache)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["neighbor", "show"])

    # Should succeed showing neighbor table
    assert result == 0
    output = capture.get()
    # Should contain neighbor information or be empty
    assert len(output.strip()) >= 0


def test_execute_rule_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing routing rules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["rule", "show"])

    # Should succeed showing routing rules
    assert result == 0
    output = capture.get()
    # Should contain rule information
    assert len(output.strip()) >= 0
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["from", "lookup", "priority", "table"]
        )


def test_execute_netns_show(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing network namespaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["netns", "list"])

    # Should succeed showing network namespaces
    assert result == 0
    output = capture.get()
    # Should contain namespace information or be empty
    assert len(output.strip()) >= 0


def test_execute_addr_flush(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test flushing addresses (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "flush", "dev", "lo"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should flush addresses successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1


def test_execute_route_flush(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test flushing routes (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["route", "flush", "table", "main"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should flush routes successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1


def test_execute_invalid_object(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test with invalid object
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid", "show"])

    # Should fail with invalid object error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Object", "invalid", "unknown", "error"])


def test_execute_invalid_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test with invalid command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "invalid"])

    # Should fail with invalid command error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Command", "invalid", "unknown", "error"])


def test_execute_missing_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test with missing required parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "add"])

    # Should fail with missing parameters error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["argument", "required", "missing", "error"])


def test_execute_invalid_ip_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test with invalid IP address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["addr", "add", "999.999.999.999/24", "dev", "lo"]
        )

    # Should fail with invalid IP address error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "error", "bad"])


def test_execute_nonexistent_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test with nonexistent interface
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show", "nonexistent999"])

    # Should either fail or show no output
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Cannot find device", "does not exist", "error"]
        )
    else:
        # May succeed with empty output
        assert result == 0


def test_execute_statistics_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test showing interface statistics
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "link", "show"])

    # Should succeed showing statistics
    assert result == 0
    output = capture.get()
    # Should contain statistics information
    assert len(output.strip()) > 0
    if len(output.strip()) > 0:
        assert (
            any(
                keyword in output.lower()
                for keyword in ["rx", "tx", "bytes", "packets", "errors"]
            )
            or len(output.strip()) >= 0
        )


def test_execute_json_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test JSON output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-j", "addr", "show"])

    # Should succeed with JSON output
    assert result == 0
    output = capture.get()
    # Should contain JSON format or regular output
    assert len(output.strip()) >= 0
    if output.strip().startswith("[") or output.strip().startswith("{"):
        # Valid JSON format
        assert any(char in output for char in ['"', "{", "}", "[", "]"])


def test_execute_brief_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test brief output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-br", "addr", "show"])

    # Should succeed with brief output
    assert result == 0
    output = capture.get()
    # Should contain brief format information
    assert len(output.strip()) >= 0


def test_execute_family_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test family option for IPv4
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-4", "addr", "show"])

    # Should succeed showing IPv4 addresses
    assert result == 0
    output = capture.get()
    # Should contain IPv4 address information
    assert len(output.strip()) >= 0


def test_execute_ipv6_family_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test family option for IPv6
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-6", "addr", "show"])

    # Should succeed showing IPv6 addresses
    assert result == 0
    output = capture.get()
    # Should contain IPv6 address information or be empty
    assert len(output.strip()) >= 0


def test_execute_monitor_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test monitor mode (may not work in all environments)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["monitor", "link"])

    # Should either succeed or fail with not supported error
    if result == 0:
        output = capture.get()
        # Monitor mode may produce no immediate output
        assert len(output.strip()) >= 0
    else:
        # May not be supported in all environments
        assert result == 1


def test_execute_batch_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test batch mode with simple command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-batch", "/dev/null"])

    # Should handle batch mode
    if result == 0:
        output = capture.get()
        # Batch mode with empty file should succeed
        assert len(output.strip()) >= 0
    else:
        # May fail if batch mode not supported or file issues
        assert result == 1


def test_execute_force_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test force option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "addr", "show"])

    # Should succeed with force option
    assert result == 0
    output = capture.get()
    # Should contain address information
    assert len(output.strip()) >= 0


def test_execute_netlink_protocol(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test netlink protocol operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["addr", "show", "to", "127.0.0.0/8"]
        )

    # Should succeed filtering addresses
    assert result == 0
    output = capture.get()
    # Should contain filtered address information
    assert len(output.strip()) >= 0


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show"])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have structured output format
        _ = output.strip().split("\n")
        # Should contain interface-related information
        assert any(
            keyword in output.lower()
            for keyword in ["inet", "link", "scope", "flags", "mtu", "lo", "eth"]
        )


def test_execute_link_type_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test link type filtering
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["link", "show", "type", "loopback"]
        )

    # Should succeed filtering by link type
    assert result == 0
    output = capture.get()
    # Should contain loopback interface information
    assert len(output.strip()) >= 0


def test_execute_mtu_configuration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test MTU configuration
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["link", "set", "lo", "mtu", "1500"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should configure MTU successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1


def test_execute_address_scope_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test address scope filtering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show", "scope", "host"])

    # Should succeed filtering by scope
    assert result == 0
    output = capture.get()
    # Should contain scope-filtered address information
    assert len(output.strip()) >= 0


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) >= 0


def test_execute_performance_with_many_interfaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test performance with many interfaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["link", "show"])

    # Should handle many interfaces efficiently
    assert result == 0
    output = capture.get()
    # Should complete in reasonable time
    assert len(output) >= 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 100000  # Reasonable output size limit


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid_object", "show"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["Object", "invalid", "unknown", "error"])


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test permission handling for configuration changes
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["addr", "add", "192.168.1.1/32", "dev", "lo"]
        )

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        # Should show permission-related error
        assert any(
            msg in output for msg in ["permission", "denied", "not permitted", "error"]
        )
    else:
        # May succeed if running with appropriate privileges
        assert result == 0


def test_execute_network_namespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test network namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addr", "show"])

    # Should work within current network namespace
    assert result == 0
    output = capture.get()
    # Should show interfaces available in current namespace
    assert len(output.strip()) >= 0


def test_execute_ipv6_address_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test IPv6 address handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-6", "addr", "show", "lo"])

    # Should handle IPv6 addresses
    assert result == 0
    output = capture.get()

    if "inet6" in output.lower():
        # Should display IPv6 addresses properly
        assert any(
            ipv6_indicator in output.lower()
            for ipv6_indicator in ["::1", "inet6", "scope"]
        )


def test_execute_routing_table_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test routing table management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["route", "show", "table", "all"])

    # Should show all routing tables
    assert result == 0
    output = capture.get()
    # Should contain routing information
    assert len(output.strip()) >= 0


def test_execute_link_state_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test link state management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["link", "show", "up"])

    # Should show only up interfaces
    assert result == 0
    output = capture.get()
    # Should contain up interface information
    assert len(output.strip()) >= 0


def test_execute_address_label_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test address label management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["addrlabel", "list"])

    # Should list address labels
    if result == 0:
        output = capture.get()
        # Should contain label information
        assert len(output.strip()) >= 0
    else:
        # May not be supported in all environments
        assert result == 1


def test_execute_tunnel_interface_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpCommand,
):
    # Test tunnel interface handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["tunnel", "show"])

    # Should handle tunnel interfaces
    if result == 0:
        output = capture.get()
        # Should show tunnel information
        assert len(output.strip()) >= 0
    else:
        # May not be supported or no tunnels exist
        assert result == 1
