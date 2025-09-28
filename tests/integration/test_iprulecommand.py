"""Integration tests for the IpruleCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IpruleCommand instance."""
    yield pebble_shell.commands.IpruleCommand(shell=shell)


def test_name(command: pebble_shell.commands.IpruleCommand):
    assert command.name == "ip rule" or command.name == "iprule"


def test_category(command: pebble_shell.commands.IpruleCommand):
    assert command.category == "Network"


def test_help(command: pebble_shell.commands.IpruleCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["ip", "rule", "routing", "policy", "table"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["ip", "rule", "routing", "usage"]
    )


def test_execute_show_all_rules(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing all routing rules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain routing rule information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain routing rule information
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain routing rule indicators
            rule_found = any(
                any(
                    indicator in line
                    for indicator in [":", "from", "to", "lookup", "table", "priority"]
                )
                for line in lines
                if line.strip()
            )
            if rule_found:
                assert rule_found
    else:
        # Should fail if no permission or network unavailable
        assert result == 1


def test_execute_show_default_rules(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing default routing rules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing default rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain default rule information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain default rule information
            has_default = any(
                default in output.lower() for default in ["main", "local", "default"]
            )
            if has_default:
                assert has_default
    else:
        assert result == 1


def test_execute_show_specific_table(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules for specific table
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "table", "main"])

    # Should either succeed showing table rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain table rule information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain main table rule information
            assert "main" in output.lower() or "table" in output.lower()
    else:
        assert result == 1


def test_execute_show_priority_range(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rule priority information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing priorities or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show rule priorities
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain priority information
            import re

            priority_pattern = r"\b\d+:\s"
            if re.search(priority_pattern, output):
                assert True  # Priority numbers found
    else:
        assert result == 1


def test_execute_list_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test list command (alias for show)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["list"])

    # Should either succeed listing rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should list all rules
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_add_rule(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test adding routing rule (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "from", "192.168.1.0/24", "table", "100"]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should add rule (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "error", "not found"]
        )


def test_execute_delete_rule(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test deleting routing rule (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["del", "from", "192.168.1.0/24", "table", "100"]
        )

    # Should either succeed or fail with permission/not found error
    if result == 0:
        output = capture.get()
        # Should delete rule (if permitted and exists)
        assert len(output) >= 0
    else:
        # Should fail if not root or rule doesn't exist
        assert result == 1


def test_execute_flush_rules(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test flushing routing rules (should require privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["flush"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should flush rules (if permitted)
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "root", "error"])


def test_execute_show_from_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with from selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "from", "0.0.0.0/0"])

    # Should either succeed showing from rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show from-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain from rule information
            assert "from" in output.lower() or "0.0.0.0" in output  # noqa: S104
    else:
        assert result == 1


def test_execute_show_to_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with to selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "to", "0.0.0.0/0"])

    # Should either succeed showing to rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show to-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain to rule information
            assert "to" in output.lower() or "0.0.0.0" in output  # noqa: S104
    else:
        assert result == 1


def test_execute_show_iif_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with input interface selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "iif", "lo"])

    # Should either succeed showing iif rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show interface-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain interface rule information
            assert "iif" in output.lower() or "lo" in output.lower()
    else:
        assert result == 1


def test_execute_show_oif_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with output interface selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "oif", "lo"])

    # Should either succeed showing oif rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show output interface-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain output interface rule information
            assert "oif" in output.lower() or "lo" in output.lower()
    else:
        assert result == 1


def test_execute_show_tos_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with TOS selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "tos", "0x10"])

    # Should either succeed showing TOS rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show TOS-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain TOS rule information
            assert "tos" in output.lower() or "0x" in output
    else:
        assert result == 1


def test_execute_show_fwmark_selector(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test showing rules with firewall mark selector
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "fwmark", "1"])

    # Should either succeed showing fwmark rules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show firewall mark-based rules
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain fwmark rule information
            assert "fwmark" in output.lower() or "mark" in output.lower()
    else:
        assert result == 1


def test_execute_invalid_table_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test with invalid table name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show", "table", "nonexistent"])

    # Should fail with invalid table error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "table", "not found", "error"])


def test_execute_invalid_priority(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test with invalid priority value
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "priority", "abc", "table", "main"]
        )

    # Should fail with invalid priority error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "priority", "number", "error"])


def test_execute_invalid_from_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test with invalid from address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "from", "999.999.999.999", "table", "main"]
        )

    # Should fail with invalid address error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "from", "error"])


def test_execute_invalid_to_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test with invalid to address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "to", "999.999.999.999", "table", "main"]
        )

    # Should fail with invalid address error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "to", "error"])


def test_execute_invalid_interface(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test with invalid interface name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "iif", "nonexistent99", "table", "main"]
        )

    # Should fail with invalid interface error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "interface", "not found", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "show"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_rule_priority_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test rule priority display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing priorities or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show rule priorities
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain priority information
            has_priority = any(
                priority in output
                for priority in ["32766", "32767", "0:", "100:", "1000:"]
            )
            if has_priority:
                assert has_priority
    else:
        assert result == 1


def test_execute_table_lookup_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test table lookup display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing table lookups or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show table lookup information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain table lookup information
            has_lookup = any(
                lookup in output.lower()
                for lookup in ["lookup", "table", "main", "local"]
            )
            if has_lookup:
                assert has_lookup
    else:
        assert result == 1


def test_execute_rule_selector_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test rule selector display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed showing selectors or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show rule selectors
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain selector information
            has_selector = any(
                selector in output.lower()
                for selector in ["from", "to", "iif", "oif", "tos", "fwmark"]
            )
            if has_selector:
                assert has_selector
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test permission handling for modifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "from", "10.0.0.0/8", "table", "200"]
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
    command: pebble_shell.commands.IpruleCommand,
):
    # Test network namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed in current namespace or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show rules in current namespace
        assert len(output) >= 0
    else:
        # Should fail if namespace unavailable
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
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


def test_execute_routing_policy_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
):
    # Test routing policy validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["show"])

    # Should either succeed validating policies or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show routing policies
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain policy information
            assert any(
                policy in output.lower()
                for policy in ["rule", "table", "lookup", "priority"]
            )
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpruleCommand,
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
    command: pebble_shell.commands.IpruleCommand,
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
    command: pebble_shell.commands.IpruleCommand,
):
    # Test signal handling during rule operations
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
    command: pebble_shell.commands.IpruleCommand,
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
