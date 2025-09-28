"""Integration tests for the CpuinfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CpuinfoCommand instance."""
    yield pebble_shell.commands.CpuinfoCommand(shell=shell)


def test_name(command: pebble_shell.commands.CpuinfoCommand):
    assert command.name == "cpuinfo [-c] [-t] [-a]"


def test_category(command: pebble_shell.commands.CpuinfoCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.CpuinfoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "cpuinfo" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "cpuinfo" in capture.get()


def test_execute_no_args_default_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed if /proc/cpuinfo is available or fail gracefully
    if result == 0:
        # Should contain CPU information panel
        output = capture.get()
        assert "CPU Information" in output
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_compact_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])

    # Should either succeed and show compact table or fail gracefully
    if result == 0:
        # Should contain table headers for compact format
        output = capture.get()
        # In compact format, we expect table headers
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_topology_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t"])

    # Should either succeed and show topology table or fail gracefully
    if result == 0:
        # Should contain table headers for topology format
        output = capture.get()
        assert any(
            header in output for header in ["CPU", "Physical ID", "Core ID", "Siblings"]
        )
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_all_cpus_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should either succeed and show all CPUs or fail gracefully
    if result == 0:
        # Should contain CPU information panel for all CPUs
        output = capture.get()
        assert "CPU Information" in output
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_multiple_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "-t"])

    # Should either succeed (flags processed in order, compact takes precedence) or fail
    if result == 0:
        # Compact format should take precedence over topology
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_all_flags_together(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "-t", "-a"])

    # Should either succeed (compact format should take precedence) or fail
    if result == 0:
        # Compact format should take precedence
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_invalid_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x"])

    # Invalid flags are ignored, should behave like no flags
    if result == 0:
        # Should show default full format
        output = capture.get()
        assert "CPU Information" in output
    else:
        # Should be 1 if /proc/cpuinfo is not accessible
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_compact_then_topology(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "-t"])

    # Compact should take precedence since it's checked first
    if result == 0:
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_topology_then_compact(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-c"])

    # Compact should still take precedence since it's checked first in code
    if result == 0:
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_all_cpus_with_compact(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "-c"])

    # Compact should take precedence over -a flag
    if result == 0:
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_all_cpus_with_topology(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "-t"])

    # Topology should take precedence over -a flag
    if result == 0:
        output = capture.get()
        assert any(
            header in output for header in ["CPU", "Physical ID", "Core ID", "Siblings"]
        )
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_proc_read_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    # This test verifies that ProcReadError is handled correctly
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # In container environments without full /proc access, should fail gracefully
    if result == 1:
        assert "Error reading CPU information" in capture.get()
    else:
        # If it succeeds, should have valid output
        assert result == 0
        assert "CPU Information" in capture.get()


def test_execute_empty_args_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    # Test explicit empty list vs no args
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should behave identically to no arguments case
    if result == 0:
        output = capture.get()
        assert "CPU Information" in output
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_flag_case_sensitivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    # Test that flags are case-sensitive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-C"])  # Capital C

    # Capital C should be ignored (treated as invalid), should show default format
    if result == 0:
        output = capture.get()
        assert "CPU Information" in output
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()


def test_execute_repeated_flags(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpuinfoCommand,
):
    # Test repeated flags
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "-c", "-c"])

    # Should work the same as single -c flag
    if result == 0:
        output = capture.get()
        assert any(header in output for header in ["CPU", "Model", "Cores", "Cache"])
    else:
        assert result == 1
        assert "Error reading CPU information" in capture.get()
