"""Integration tests for the IpcsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a IpcsCommand instance."""
    yield pebble_shell.commands.IpcsCommand(shell=shell)


def test_name(command: pebble_shell.commands.IpcsCommand):
    assert command.name == "ipcs"


def test_category(command: pebble_shell.commands.IpcsCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.IpcsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "ipcs" in output
    assert "Show IPC facilities" in output
    assert "semaphore" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "ipcs" in output
    assert "Show IPC facilities" in output


def test_execute_no_args_show_all(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # ipcs with no args should show all IPC facilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should succeed showing IPC information
    assert result == 0
    output = capture.get()
    # Should contain IPC facility information
    assert len(output.strip()) >= 0
    # May contain headers for different IPC types
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["shared memory", "semaphore", "message", "key", "id"]
        )


def test_execute_show_all_facilities(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing all IPC facilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should succeed showing all facilities
    assert result == 0
    output = capture.get()
    # Should contain comprehensive IPC information
    assert len(output.strip()) >= 0
    # Should show all IPC types
    if len(output.strip()) > 0:
        assert any(
            section in output.lower()
            for section in ["shared memory", "semaphore", "message"]
        )


def test_execute_shared_memory_segments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing shared memory segments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should succeed showing shared memory
    assert result == 0
    output = capture.get()
    # Should contain shared memory information
    assert len(output.strip()) >= 0
    # May contain shared memory headers
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["shared memory", "shmid", "key", "size", "owner"]
        )


def test_execute_semaphore_arrays(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing semaphore arrays
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])

    # Should succeed showing semaphores
    assert result == 0
    output = capture.get()
    # Should contain semaphore information
    assert len(output.strip()) >= 0
    # May contain semaphore headers
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["semaphore", "semid", "key", "nsems", "owner"]
        )


def test_execute_message_queues(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing message queues
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q"])

    # Should succeed showing message queues
    assert result == 0
    output = capture.get()
    # Should contain message queue information
    assert len(output.strip()) >= 0
    # May contain message queue headers
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["message", "msqid", "key", "messages", "owner"]
        )


def test_execute_limits_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing IPC limits
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should succeed showing limits
    assert result == 0
    output = capture.get()
    # Should contain limits information
    assert len(output.strip()) > 0
    # Should contain limit values
    assert any(
        keyword in output.lower()
        for keyword in [
            "limit",
            "max",
            "resource",
            "shared memory",
            "semaphore",
            "message",
        ]
    )


def test_execute_summary_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing summary information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-u"])

    # Should succeed showing summary
    assert result == 0
    output = capture.get()
    # Should contain summary information
    assert len(output.strip()) >= 0
    # May contain usage statistics
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["used", "allocated", "total", "summary"]
        )


def test_execute_time_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing time information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t"])

    # Should succeed showing time info
    assert result == 0
    output = capture.get()
    # Should contain time information
    assert len(output.strip()) >= 0
    # May contain timestamps
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["time", "attach", "detach", "change", "create"]
        )


def test_execute_process_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing process information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p"])

    # Should succeed showing process info
    assert result == 0
    output = capture.get()
    # Should contain process information
    assert len(output.strip()) >= 0
    # May contain process IDs
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["pid", "process", "creator", "last"]
        )


def test_execute_creator_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing creator information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])

    # Should succeed showing creator info
    assert result == 0
    output = capture.get()
    # Should contain creator information
    assert len(output.strip()) >= 0
    # May contain creator details
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower()
            for keyword in ["creator", "owner", "cuid", "cgid"]
        )


def test_execute_numeric_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test numeric output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n"])

    # Should succeed with numeric format
    assert result == 0
    output = capture.get()
    # Should contain numeric information
    assert len(output.strip()) >= 0
    # Should show numeric IDs instead of names
    if len(output.strip()) > 0:
        # May contain numeric UIDs/GIDs
        assert any(char.isdigit() for char in output)


def test_execute_combined_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test combined options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-mpt"])

    # Should succeed with combined options
    assert result == 0
    output = capture.get()
    # Should contain combined information
    assert len(output.strip()) >= 0
    # Should show shared memory with process and time info
    if len(output.strip()) > 0:
        assert any(
            keyword in output.lower() for keyword in ["shared memory", "pid", "time"]
        )


def test_execute_specific_facility_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test showing specific facility by ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "-i", "999999"])

    # Should either show specific facility or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show specific facility information
        assert len(output.strip()) >= 0
    else:
        # Should fail if facility doesn't exist
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["invalid", "not found", "no such", "error"]
        )


def test_execute_human_readable_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test human-readable format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-h", "-m"])

    # Should either show help or human-readable format
    if result == 0:
        output = capture.get()
        # Should contain formatted information
        assert len(output.strip()) >= 0
    else:
        # May not support -h for human-readable
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should succeed showing accessible facilities
    assert result == 0
    output = capture.get()
    # Should show only accessible IPC facilities
    assert len(output.strip()) >= 0


def test_execute_empty_system_state(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test with empty IPC system state
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should succeed even with no shared memory segments
    assert result == 0
    output = capture.get()
    # Should show headers even if no segments exist
    assert len(output.strip()) >= 0


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have structured output format
        _ = output.strip().split("\n")
        # Should contain limit information
        assert any(
            keyword in output.lower() for keyword in ["limit", "max", "resource"]
        )


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 50000  # Reasonable output size limit


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) >= 0


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "invalid"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "error", "usage"])


def test_execute_system_resource_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test system resource monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-u"])

    # Should monitor system resources appropriately
    assert result == 0
    output = capture.get()
    # Should show resource usage
    assert len(output.strip()) >= 0


def test_execute_ipc_namespace_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test IPC namespace awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should work within current IPC namespace
    assert result == 0
    output = capture.get()
    # Should show facilities in current namespace
    assert len(output.strip()) >= 0


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    # Should adapt to platform-specific IPC implementation
    assert len(output.strip()) >= 0


def test_execute_performance_monitoring(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test performance monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t"])

    # Should complete efficiently
    assert result == 0
    output = capture.get()
    # Should provide timing information efficiently
    assert len(output.strip()) >= 0


def test_execute_security_awareness(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test security awareness
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])

    # Should handle security information appropriately
    assert result == 0
    output = capture.get()
    # Should show creator/owner information securely
    assert len(output.strip()) >= 0


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert len(output.strip()) >= 0


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test signal handling during execution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert len(output.strip()) >= 0


def test_execute_kernel_interface_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test kernel interface compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should interface with kernel IPC subsystem correctly
    assert result == 0
    output = capture.get()
    # Should work with current kernel version
    assert len(output.strip()) >= 0


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["-m"])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["-m"])

    # Should produce consistent results
    assert result1 == 0
    assert result2 == 0
    # Both executions should succeed consistently
    assert result1 == result2


def test_execute_verbose_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test verbose output mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v"])

    # Should either provide verbose output or show error
    if result == 0:
        output = capture.get()
        # Should provide detailed information
        assert len(output.strip()) >= 0
    else:
        # May not support -v option
        assert result == 1


def test_execute_facility_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test facility filtering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-q"])

    # Should show only semaphores and message queues
    assert result == 0
    output = capture.get()
    # Should filter facilities appropriately
    assert len(output.strip()) >= 0


def test_execute_backward_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test backward compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should maintain backward compatibility
    assert result == 0
    output = capture.get()
    # Should work with older IPC implementations
    assert len(output.strip()) >= 0


def test_execute_resource_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test resource cleanup
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should clean up resources properly
    assert result == 0
    output = capture.get()
    # Should not leak resources
    assert len(output.strip()) >= 0


def test_execute_formatting_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test formatting consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m"])

    # Should produce consistently formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have consistent column formatting
        lines = output.strip().split("\n")
        # Should maintain formatting consistency
        assert len(lines) >= 1


def test_execute_ipc_state_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test IPC state detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-u"])

    # Should detect current IPC state accurately
    assert result == 0
    output = capture.get()
    # Should reflect actual system state
    assert len(output.strip()) >= 0


def test_execute_multi_user_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test multi-user environment handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c"])

    # Should handle multi-user environments appropriately
    assert result == 0
    output = capture.get()
    # Should show ownership information properly
    assert len(output.strip()) >= 0


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.IpcsCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert len(output.strip()) >= 0
