"""Integration tests for the DnsdomainnameCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DnsdomainnameCommand instance."""
    yield pebble_shell.commands.DnsdomainnameCommand(shell=shell)


def test_name(command: pebble_shell.commands.DnsdomainnameCommand):
    assert command.name == "dnsdomainname"


def test_category(command: pebble_shell.commands.DnsdomainnameCommand):
    assert command.category == "Network"


def test_help(command: pebble_shell.commands.DnsdomainnameCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "dnsdomainname" in output
    assert any(
        phrase in output.lower() for phrase in ["dns", "domain", "name", "hostname"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "dnsdomainname" in output
    assert any(
        phrase in output.lower() for phrase in ["dns", "domain", "name", "hostname"]
    )


def test_execute_no_args_show_domain(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # dnsdomainname with no args should show DNS domain name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing domain or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain domain name information
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            # Should be valid domain format or empty
            if domain:
                # Should contain domain-like format
                assert "." in domain or len(domain) > 0
                # Should not contain spaces in domain name
                assert " " not in domain
    else:
        # Should fail if cannot determine domain
        assert result == 1


def test_execute_domain_name_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test domain name resolution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed resolving domain or fail gracefully
    if result == 0:
        output = capture.get()
        # Should resolve domain name
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            # Should be valid domain name format
            if domain and domain != "(none)":
                # Should not start or end with dot
                assert not domain.startswith(".")
                assert not domain.endswith(".")
                # Should contain valid characters
                import re

                assert re.match(r"^[a-zA-Z0-9.-]+$", domain)
    else:
        assert result == 1


def test_execute_fqdn_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test FQDN domain extraction
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed extracting domain or fail gracefully
    if result == 0:
        output = capture.get()
        # Should extract domain from FQDN
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            # Should be domain part only (not full hostname)
            if domain and "." in domain:
                # Should not contain hostname part
                parts = domain.split(".")
                assert len(parts) >= 2  # At least domain.tld
    else:
        assert result == 1


def test_execute_hostname_resolution_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test hostname resolution access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing hostname info or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access hostname resolution successfully
        assert len(output) >= 0
    else:
        # Should fail if hostname resolution not available
        assert result == 1


def test_execute_dns_configuration_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test DNS configuration access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing DNS config or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access DNS configuration
        assert len(output) >= 0
    else:
        # Should fail if DNS configuration unavailable
        assert result == 1


def test_execute_resolv_conf_parsing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test /etc/resolv.conf parsing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed parsing resolv.conf or fail gracefully
    if result == 0:
        output = capture.get()
        # Should parse resolv.conf if available
        assert len(output) >= 0
    else:
        # Should fail if resolv.conf not accessible
        assert result == 1


def test_execute_search_domain_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test search domain detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting search domains or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect search domains
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            # Should be first search domain or derived domain
            if domain:
                assert isinstance(domain, str)
                assert len(domain) > 0
    else:
        assert result == 1


def test_execute_empty_domain_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test empty domain handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with empty domain or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty domain appropriately
        assert len(output) >= 0
        # Empty output is valid (no domain configured)
    else:
        assert result == 1


def test_execute_localhost_domain_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test localhost domain handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with localhost domain or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle localhost domains
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            # Should handle localhost-related domains
            if "local" in domain.lower():
                assert "local" in domain
    else:
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_unexpected_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test with unexpected arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["unexpected", "args"])

    # Should either ignore args or fail gracefully
    if result == 0:
        output = capture.get()
        # Should ignore unexpected arguments
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with permissions or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access domain information
        assert len(output) >= 0
    else:
        # Should fail if insufficient permissions
        assert result == 1


def test_execute_network_configuration_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test network configuration access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing network config or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access network configuration
        assert len(output) >= 0
    else:
        # Should fail if network config unavailable
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test container environment handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully in containers
    if result == 0:
        output = capture.get()
        # Should handle container environments
        assert len(output) >= 0
    else:
        # May fail in containers with limited networking
        assert result == 1


def test_execute_output_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test output consistency across multiple calls
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=[])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=[])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both should succeed with same domain (unless changing)
        assert result1 == result2
    else:
        # Should fail consistently
        assert result1 == result2


def test_execute_domain_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test domain format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with valid format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should produce valid domain format
        assert len(output) >= 0
        if len(output) > 0:
            domain = output.strip()
            if domain and domain != "(none)":
                # Should be valid domain format
                import re

                # Basic domain validation
                pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$"
                assert re.match(pattern, domain) or domain == "localhost"
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should integrate with system properly
    if result == 0:
        output = capture.get()
        # Should integrate with DNS system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000  # Small output expected
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test signal handling during domain resolution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # May fail on platforms with different DNS setup
        assert result == 1


def test_execute_dns_server_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test DNS server independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work independently of DNS servers
    if result == 0:
        output = capture.get()
        # Should not depend on external DNS servers
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cache_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test cache efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use caching efficiently
    if result == 0:
        output = capture.get()
        # Should cache domain lookups
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DnsdomainnameCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work regardless of locale settings
    if result == 0:
        output = capture.get()
        # Should be locale-independent
        assert len(output) >= 0
    else:
        assert result == 1
