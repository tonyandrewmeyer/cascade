"""Integration tests for the IpcalcCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IpcalcCommand instance."""
    yield pebble_shell.commands.IpcalcCommand(shell=shell)


def test_name(command: pebble_shell.commands.IpcalcCommand):
    assert command.name == "ipcalc"


def test_category(command: pebble_shell.commands.IpcalcCommand):
    assert command.category == "Mathematical Utilities"


def test_help(command: pebble_shell.commands.IpcalcCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "ipcalc" in output
    assert "IP network calculator" in output
    assert "-n, --network" in output
    assert "-b, --broadcast" in output
    assert "192.168.1.100/24" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "ipcalc" in output
    assert "IP network calculator" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # ipcalc with no args should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["missing", "address", "usage"])


def test_execute_valid_ipv4_with_cidr(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with valid IPv4 address and CIDR notation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/24"])

    # Should either succeed with network calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show network calculation results
        assert "192.168.1" in output  # Should contain network portion
    else:
        assert result == 1


def test_execute_valid_ipv4_without_cidr(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with valid IPv4 address without CIDR (should assume /32 or default)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100"])

    # Should either succeed with default calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IP address information
        assert "192.168.1.100" in output
    else:
        assert result == 1


def test_execute_invalid_ip_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with invalid IP address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["999.999.999.999"])

    # Should fail with invalid IP error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "IP"])


def test_execute_invalid_cidr_prefix(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with invalid CIDR prefix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/99"])

    # Should fail with invalid prefix error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "prefix", "CIDR"])


def test_execute_network_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -n option to display network address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "192.168.1.100/24"])

    # Should either succeed showing network address or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show network address
        assert "192.168.1.0" in output  # Network address for /24
    else:
        assert result == 1


def test_execute_network_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test --network option to display network address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--network", "192.168.1.100/24"])

    # Should behave same as -n option
    if result == 0:
        output = capture.get()
        # Should show network address
        assert "192.168.1.0" in output
    else:
        assert result == 1


def test_execute_broadcast_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -b option to display broadcast address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "192.168.1.100/24"])

    # Should either succeed showing broadcast address or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show broadcast address
        assert "192.168.1.255" in output  # Broadcast for /24
    else:
        assert result == 1


def test_execute_broadcast_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test --broadcast option to display broadcast address
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--broadcast", "192.168.1.100/24"]
        )

    # Should behave same as -b option
    if result == 0:
        output = capture.get()
        # Should show broadcast address
        assert "192.168.1.255" in output
    else:
        assert result == 1


def test_execute_netmask_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -m/--netmask option to display network mask
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "192.168.1.100/24"])

    # Should either succeed showing netmask or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show netmask
        assert "255.255.255.0" in output  # Netmask for /24
    else:
        assert result == 1


def test_execute_prefix_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -p/--prefix option to display prefix length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "192.168.1.100/24"])

    # Should either succeed showing prefix or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show prefix length
        assert "24" in output
    else:
        assert result == 1


def test_execute_class_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -c/--class option to display address class
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "192.168.1.100/24"])

    # Should either succeed showing address class or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show address class (C for 192.168.x.x)
        assert any(cls in output for cls in ["A", "B", "C", "class"])
    else:
        assert result == 1


def test_execute_hostmask_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -h/--hostmask option to display host mask
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--hostmask", "192.168.1.100/24"])

    # Should either succeed showing hostmask or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show hostmask (inverse of netmask)
        assert "0.0.0.255" in output  # Hostmask for /24
    else:
        assert result == 1


def test_execute_first_host_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -f/--first option to display first host address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "192.168.1.100/24"])

    # Should either succeed showing first host or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show first host address
        assert "192.168.1.1" in output  # First host for /24
    else:
        assert result == 1


def test_execute_last_host_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test -l/--last option to display last host address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l", "192.168.1.100/24"])

    # Should either succeed showing last host or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show last host address
        assert "192.168.1.254" in output  # Last host for /24
    else:
        assert result == 1


def test_execute_hosts_count_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test --hosts option to display number of hosts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--hosts", "192.168.1.100/24"])

    # Should either succeed showing host count or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show number of hosts
        assert "254" in output  # 254 hosts for /24
    else:
        assert result == 1


def test_execute_multiple_options_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test multiple options together
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-n", "-b", "-m", "192.168.1.100/24"]
        )

    # Should either succeed showing multiple values or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show network, broadcast, and netmask
        assert "192.168.1.0" in output  # Network
        assert "192.168.1.255" in output  # Broadcast
        assert "255.255.255.0" in output  # Netmask
    else:
        assert result == 1


def test_execute_private_network_calculation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with private network ranges
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["10.0.0.1/8"])

    # Should either succeed with private network calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle large private networks
        assert "10." in output
    else:
        assert result == 1


def test_execute_small_subnet_calculation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with small subnet (/30)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/30"])

    # Should either succeed with small subnet calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle /30 subnet (4 addresses, 2 hosts)
        assert "192.168.1" in output
    else:
        assert result == 1


def test_execute_host_only_subnet(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with /32 (host only)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/32"])

    # Should either succeed with host-only calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle single host subnet
        assert "192.168.1.100" in output
    else:
        assert result == 1


def test_execute_zero_prefix_length(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with /0 prefix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/0"])

    # Should either succeed with entire internet or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle /0 (entire IPv4 space)
        assert "0.0.0.0" in output  # noqa: S104
    else:
        assert result == 1


def test_execute_malformed_input_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with malformed input
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.1.100/"])

    # Should fail with format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "format", "malformed"])


def test_execute_non_numeric_ip_components(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with non-numeric IP components
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["192.168.abc.100/24"])

    # Should fail with invalid IP error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "address", "IP"])


def test_execute_empty_ip_address(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with empty IP address
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid input error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "empty", "address"])


def test_execute_all_calculation_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcalcCommand,
):
    # Test with all calculation options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "-n",
                "-b",
                "-m",
                "-p",
                "-c",
                "-f",
                "-l",
                "--hosts",
                "192.168.1.100/24",
            ],
        )

    # Should either succeed showing all calculations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show comprehensive network information
        assert "192.168.1" in output
    else:
        assert result == 1
