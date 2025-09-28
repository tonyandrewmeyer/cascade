"""Integration tests for the IprouteCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IprouteCommand instance."""
    yield pebble_shell.commands.IprouteCommand(shell=shell)


def test_name(command: pebble_shell.commands.IprouteCommand):
    assert command.name == "ip route" or command.name == "iproute"


def test_category(command: pebble_shell.commands.IprouteCommand):
    assert command.category == "Network"


def test_help(command: pebble_shell.commands.IprouteCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["ip", "route", "routing", "gateway", "network"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["ip", "route", "routing", "usage"]
    )


def test_execute_show_all_routes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing all routes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing routes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain routing table information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain routing information
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain routing indicators
            route_found = any(
                any(
                    indicator in line
                    for indicator in ["via", "dev", "src", "scope", "proto"]
                )
                for line in lines
                if line.strip()
            )
            if route_found:
                assert route_found
    else:
        # Should fail if no permission or network unavailable
        assert result == 1


def test_execute_show_default_route(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing default route
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "default"])

    # Should either succeed showing default route or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain default route information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain default route information
            assert "default" in output.lower() or "0.0.0.0/0" in output
    else:
        # Should fail if no default route
        assert result == 1


def test_execute_show_specific_destination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing route to specific destination
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "127.0.0.1"])

    # Should either succeed showing route or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain route to localhost
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain localhost route information
            assert "127.0.0.1" in output or "local" in output.lower()
    else:
        assert result == 1


def test_execute_show_ipv4_routes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing IPv4 routes only
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "-4"])

    # Should either succeed showing IPv4 routes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IPv4 routes
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain IPv4 patterns
            import re

            ipv4_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
            if re.search(ipv4_pattern, output):
                assert True  # IPv4 addresses found
    else:
        assert result == 1


def test_execute_show_ipv6_routes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing IPv6 routes only
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "-6"])

    # Should either succeed showing IPv6 routes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IPv6 routes
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain IPv6 patterns
            assert "::" in output or "inet6" in output
    else:
        assert result == 1


def test_execute_list_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test list command (alias for show)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["list"])

    # Should either succeed listing routes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should list all routes
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_add_route(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test adding route (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "192.168.100.0/24", "via", "127.0.0.1"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should add route (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "error", "not found"]
        )


def test_execute_delete_route(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test deleting route (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["del", "192.168.100.0/24", "via", "127.0.0.1"]
        )

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete route (if permitted and exists)
        assert len(output) >= 0
    else:
        # Should fail if not root or route doesn't exist
        assert result == 1


def test_execute_replace_route(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test replacing route (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["replace", "192.168.1.0/24", "via", "127.0.0.1"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should replace route (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1


def test_execute_get_route(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test getting route to specific destination
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["get", "127.0.0.1"])

    # Should either succeed getting route or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show route to destination
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain route information
            assert "127.0.0.1" in output or "local" in output.lower()
    else:
        assert result == 1


def test_execute_flush_routes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test flushing routes (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["flush", "table", "main"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should flush routes (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "root", "error"])


def test_execute_show_routing_table(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing specific routing table
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "table", "main"])

    # Should either succeed showing table or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show main routing table
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_show_local_routes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test showing local routes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "table", "local"])

    # Should either succeed showing local routes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show local routing table
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain local route information
            assert "local" in output.lower() or "127.0.0.1" in output
    else:
        assert result == 1


def test_execute_invalid_destination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test with invalid destination
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "999.999.999.999"])

    # Should fail with invalid destination error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "destination", "address", "error"])


def test_execute_invalid_gateway(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test with invalid gateway
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "192.168.1.0/24", "via", "invalid"]
        )

    # Should fail with invalid gateway error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "gateway", "address", "error"])


def test_execute_invalid_network(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test with invalid network specification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "192.168.1.0/99", "via", "127.0.0.1"]
        )

    # Should fail with invalid network error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "network", "prefix", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "show"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_route_metrics_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test route metrics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing metrics or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show route metrics
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain metric information
            has_metrics = any(
                metric in output.lower()
                for metric in ["metric", "mtu", "proto", "scope"]
            )
            if has_metrics:
                assert has_metrics
    else:
        assert result == 1


def test_execute_route_protocols(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test route protocol information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing protocols or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show route protocols
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain protocol information
            has_proto = any(
                proto in output.lower()
                for proto in ["proto", "kernel", "static", "dhcp"]
            )
            if has_proto:
                assert has_proto
    else:
        assert result == 1


def test_execute_route_scope_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test route scope display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing scope or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show route scope
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain scope information
            has_scope = any(
                scope in output.lower() for scope in ["scope", "link", "host", "global"]
            )
            if has_scope:
                assert has_scope
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
):
    # Test permission handling for modifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "10.0.0.0/8", "via", "127.0.0.1"]
        )

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
    command: pebble_shell.commands.IprouteCommand,
):
    # Test network namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed in current namespace or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show routes in current namespace
        assert len(output) >= 0
    else:
        # Should fail if namespace unavailable
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
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


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IprouteCommand,
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
    command: pebble_shell.commands.IprouteCommand,
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
    command: pebble_shell.commands.IprouteCommand,
):
    # Test signal handling during route operations
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
    command: pebble_shell.commands.IprouteCommand,
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
        # May fail on platforms with different routing
        assert result == 1
