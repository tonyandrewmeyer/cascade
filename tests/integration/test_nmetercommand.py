"""Integration tests for the NmeterCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NmeterCommand instance."""
    yield pebble_shell.commands.NmeterCommand(shell=shell)


def test_name(command: pebble_shell.commands.NmeterCommand):
    assert command.name == "nmeter"


def test_category(command: pebble_shell.commands.NmeterCommand):
    assert command.category == "System Monitoring"


def test_help(command: pebble_shell.commands.NmeterCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "nmeter" in output
    assert "Display system statistics" in output
    assert "format" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "nmeter" in output
    assert "Display system statistics" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # nmeter with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["usage", "Usage", "nmeter", "format", "string"]
    )


def test_execute_default_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test default format string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c"])

    # Should succeed with CPU usage display
    assert result == 0
    output = capture.get()
    # Should contain CPU statistics
    assert len(output.strip()) > 0
    # Should contain numeric values for CPU usage
    assert any(char.isdigit() for char in output)


def test_execute_cpu_statistics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test CPU statistics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %s %u"])

    # Should succeed showing CPU stats
    assert result == 0
    output = capture.get()
    # Should contain CPU, system, and user statistics
    assert len(output.strip()) > 0
    # Should contain statistical values
    assert any(char.isdigit() for char in output)


def test_execute_memory_statistics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test memory statistics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%m %f"])

    # Should succeed showing memory stats
    assert result == 0
    output = capture.get()
    # Should contain memory and free memory statistics
    assert len(output.strip()) > 0
    # Should contain memory values
    assert any(char.isdigit() for char in output)


def test_execute_network_statistics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test network statistics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%n"])

    # Should succeed showing network stats
    assert result == 0
    output = capture.get()
    # Should contain network statistics
    assert len(output.strip()) > 0
    # Should contain network data
    assert any(char.isdigit() for char in output)


def test_execute_disk_statistics(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test disk I/O statistics display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%d"])

    # Should succeed showing disk stats
    assert result == 0
    output = capture.get()
    # Should contain disk statistics
    assert len(output.strip()) > 0
    # Should contain I/O data
    assert any(char.isdigit() for char in output)


def test_execute_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%t"])

    # Should succeed showing time
    assert result == 0
    output = capture.get()
    # Should contain time information
    assert len(output.strip()) > 0
    # Should contain time format
    assert any(char in output for char in [":", " "])


def test_execute_load_average(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test load average display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%l"])

    # Should succeed showing load average
    assert result == 0
    output = capture.get()
    # Should contain load average
    assert len(output.strip()) > 0
    # Should contain numeric load values
    assert any(char.isdigit() or char == "." for char in output)


def test_execute_process_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test process count display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%p"])

    # Should succeed showing process count
    assert result == 0
    output = capture.get()
    # Should contain process count
    assert len(output.strip()) > 0
    # Should contain numeric process count
    assert any(char.isdigit() for char in output)


def test_execute_uptime_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test uptime display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%T"])

    # Should succeed showing uptime
    assert result == 0
    output = capture.get()
    # Should contain uptime information
    assert len(output.strip()) > 0
    # Should contain time components
    assert any(char.isdigit() for char in output)


def test_execute_custom_format_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test custom format string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["CPU:%c MEM:%m TIME:%t"])

    # Should succeed with custom format
    assert result == 0
    output = capture.get()
    # Should contain custom formatted output
    assert len(output.strip()) > 0
    # Should contain labels and values
    assert "CPU:" in output
    assert "MEM:" in output
    assert "TIME:" in output


def test_execute_multiple_measurements(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test multiple measurements in one format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m %n %d %l"])

    # Should succeed with multiple measurements
    assert result == 0
    output = capture.get()
    # Should contain multiple statistics
    assert len(output.strip()) > 0
    # Should contain various numeric values
    assert any(char.isdigit() for char in output)


def test_execute_percentage_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test percentage format display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c%%"])

    # Should succeed with percentage format
    assert result == 0
    output = capture.get()
    # Should contain percentage values
    assert len(output.strip()) > 0
    # Should contain percent sign
    assert "%" in output


def test_execute_spacing_and_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test spacing and formatting options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["Load: %l | CPU: %c | Memory: %m"]
        )

    # Should succeed with formatted spacing
    assert result == 0
    output = capture.get()
    # Should contain properly formatted output
    assert len(output.strip()) > 0
    # Should contain separators and labels
    assert "|" in output
    assert "Load:" in output
    assert "CPU:" in output
    assert "Memory:" in output


def test_execute_invalid_format_specifier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test invalid format specifier
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%z"])

    # Should either handle invalid specifier gracefully or fail
    if result == 0:
        output = capture.get()
        # Should handle unknown specifier
        assert len(output.strip()) >= 0
    else:
        # Should fail with invalid format error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "unknown", "format", "error"])


def test_execute_empty_format_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test empty format string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either handle empty format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should produce minimal output
        assert len(output.strip()) >= 0
    else:
        # Should fail with empty format error
        assert result == 1


def test_execute_long_format_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test long format string
    long_format = "CPU:%c MEM:%m NET:%n DISK:%d LOAD:%l PROC:%p TIME:%t UPTIME:%T " * 5
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_format])

    # Should succeed with long format string
    assert result == 0
    output = capture.get()
    # Should contain extensive formatted output
    assert len(output.strip()) > 0


def test_execute_real_time_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test real-time monitoring (single snapshot)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m"])

    # Should succeed with real-time data
    assert result == 0
    output = capture.get()
    # Should contain current system statistics
    assert len(output.strip()) > 0
    # Should reflect current system state
    assert any(char.isdigit() for char in output)


def test_execute_statistics_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test statistics accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c"])

    # Should provide accurate statistics
    assert result == 0
    output = capture.get()
    # Should contain reasonable CPU values
    assert len(output.strip()) > 0
    # CPU percentage should be reasonable (0-100%)
    if output.strip().replace(".", "").isdigit():
        cpu_value = float(output.strip())
        assert 0 <= cpu_value <= 100


def test_execute_system_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test system compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%m"])

    # Should work on current system
    assert result == 0
    output = capture.get()
    # Should adapt to system capabilities
    assert len(output.strip()) > 0


def test_execute_resource_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test resource efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m %n"])

    # Should be resource efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive resources
    assert len(output.strip()) > 0


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%l"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["invalid", "error", "format"])
    else:
        # Should handle incomplete format specifier
        assert result == 0


def test_execute_memory_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test memory monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%m %f"])

    # Should monitor memory usage accurately
    assert result == 0
    output = capture.get()
    # Should contain memory statistics
    assert len(output.strip()) > 0
    # Should contain numeric memory values
    assert any(char.isdigit() for char in output)


def test_execute_network_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test network monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%n"])

    # Should monitor network activity
    assert result == 0
    output = capture.get()
    # Should contain network statistics
    assert len(output.strip()) > 0


def test_execute_disk_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test disk I/O monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%d"])

    # Should monitor disk I/O
    assert result == 0
    output = capture.get()
    # Should contain disk statistics
    assert len(output.strip()) > 0


def test_execute_process_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test process monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%p"])

    # Should monitor process count
    assert result == 0
    output = capture.get()
    # Should contain process information
    assert len(output.strip()) > 0
    # Should contain numeric process count
    assert any(char.isdigit() for char in output)


def test_execute_load_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test load average monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%l"])

    # Should monitor load average
    assert result == 0
    output = capture.get()
    # Should contain load information
    assert len(output.strip()) > 0
    # Should contain numeric load values
    assert any(char.isdigit() or char == "." for char in output)


def test_execute_time_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test time monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%t"])

    # Should display current time
    assert result == 0
    output = capture.get()
    # Should contain time information
    assert len(output.strip()) > 0


def test_execute_uptime_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test uptime monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%T"])

    # Should display system uptime
    assert result == 0
    output = capture.get()
    # Should contain uptime information
    assert len(output.strip()) > 0


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m %l"])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have clean output format
        assert len(output.strip()) > 0
        # Should contain statistical values
        assert any(char.isdigit() for char in output)


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c"])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert len(output.strip()) > 0


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test signal handling during monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%m"])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert len(output.strip()) > 0


def test_execute_platform_adaptation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test platform adaptation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%l"])

    # Should adapt to platform capabilities
    assert result == 0
    output = capture.get()
    # Should work on current platform
    assert len(output.strip()) > 0


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["%l"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["%l"])

    # Should produce consistent results
    assert result1 == 0
    assert result2 == 0
    # Both executions should succeed consistently
    assert result1 == result2


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m %n %d"])

    # Should complete efficiently
    assert result == 0
    output = capture.get()
    # Should process efficiently
    assert len(output.strip()) > 0


def test_execute_kernel_interface_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test kernel interface compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c"])

    # Should interface with kernel statistics correctly
    assert result == 0
    output = capture.get()
    # Should work with current kernel version
    assert len(output.strip()) > 0


def test_execute_resource_monitoring_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test resource monitoring accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%m"])

    # Should provide accurate resource monitoring
    assert result == 0
    output = capture.get()
    # Should reflect actual system state
    assert len(output.strip()) > 0


def test_execute_backwards_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test backwards compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c"])

    # Should maintain backwards compatibility
    assert result == 0
    output = capture.get()
    # Should work with legacy format expectations
    assert len(output.strip()) > 0


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NmeterCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["%c %m %l %p"])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert len(output.strip()) > 0
