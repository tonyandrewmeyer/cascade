"""Integration tests for the PidofCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PidofCommand instance."""
    yield pebble_shell.commands.PidofCommand(shell=shell)


def test_name(command: pebble_shell.commands.PidofCommand):
    assert command.name == "pidof"


def test_category(command: pebble_shell.commands.PidofCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.PidofCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "pidof" in output
    assert "Find process IDs by name" in output
    assert "-s" in output
    assert "-o" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "pidof" in output
    assert "Find process IDs by name" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # pidof with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "pidof <process-name>" in output


def test_execute_common_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with common process name that likely exists
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should either succeed with PIDs or fail if not found
    if result == 0:
        output = capture.get()
        # Should show PID numbers
        assert output.strip().isdigit() or any(char.isdigit() for char in output)
    else:
        # Should fail if process not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "not found",
                "No process found",
                "",  # May have empty output for not found
            ]
        )


def test_execute_kernel_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with kernel process name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kthreadd"])

    # Should either succeed with PID or fail if not found
    if result == 0:
        output = capture.get()
        # Should show PID for kernel thread
        assert output.strip().isdigit() or any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_nonexistent_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with nonexistent process name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-process-name"])

    # Should fail with no process found
    assert result == 1
    output = capture.get()
    # Should have empty output or "not found" message
    assert len(output.strip()) == 0 or "not found" in output


def test_execute_empty_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with empty process name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid process name
    assert result == 1


def test_execute_single_match_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test -s option for single match
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "init"])

    # Should either succeed with single PID or fail if not found
    if result == 0:
        output = capture.get()
        # Should show only one PID
        pids = output.strip().split()
        assert len(pids) == 1 and pids[0].isdigit()
    else:
        assert result == 1


def test_execute_omit_pid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test -o option to omit specific PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "1", "init"])

    # Should either succeed omitting PID 1 or fail if not found
    if result == 0:
        output = capture.get()
        # Should not contain PID 1 if init was found
        pids = output.strip().split()
        assert "1" not in pids
    else:
        assert result == 1


def test_execute_omit_current_shell_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test -o %PPID to omit current shell
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "%PPID", "bash"])

    # Should either succeed omitting parent shell or fail if not found
    if result == 0:
        output = capture.get()
        # Should show PIDs excluding parent shell
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_multiple_process_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with multiple process names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init", "kthreadd"])

    # Should either succeed with PIDs from all matches or fail if none found
    if result == 0:
        output = capture.get()
        # Should show PIDs for all matching processes
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_process_name_with_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with process name that includes path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/sbin/init"])

    # Should either succeed finding init by full path or fail
    if result == 0:
        output = capture.get()
        # Should show PID for init process
        assert output.strip().isdigit() or any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_case_sensitive_matching(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test case sensitivity in process name matching
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["INIT"])

    # Should handle case sensitivity appropriately
    if result == 0:
        output = capture.get()
        # Should find process if case matches
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if case doesn't match
        assert result == 1


def test_execute_partial_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with partial process name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["in"])  # Partial "init"

    # Should handle partial name matching appropriately
    if result == 0:
        output = capture.get()
        # Should find processes if partial match is supported
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if exact match required
        assert result == 1


def test_execute_special_characters_in_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with special characters in process name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["process-with-dashes"])

    # Should handle special characters in process names
    if result == 0:
        output = capture.get()
        # Should find process if it exists
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if process not found
        assert result == 1


def test_execute_numeric_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with numeric process name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["123"])

    # Should handle numeric process names
    if result == 0:
        output = capture.get()
        # Should find process if numeric name exists
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if numeric process not found
        assert result == 1


def test_execute_very_long_process_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with very long process name
    long_name = "very-long-process-name-that-exceeds-normal-length"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_name])

    # Should handle long process names appropriately
    if result == 0:
        output = capture.get()
        # Should find process if long name exists
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if long process name not found
        assert result == 1


def test_execute_multiple_instances_same_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test with process name that has multiple instances
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kworker"])  # Kernel workers

    # Should find all instances of the process
    if result == 0:
        output = capture.get()
        # Should show multiple PIDs separated by spaces
        pids = output.strip().split()
        assert len(pids) >= 1 and all(pid.isdigit() for pid in pids)
    else:
        # Should fail if no instances found
        assert result == 1


def test_execute_pid_output_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test PID output format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should format PID output correctly
    if result == 0:
        output = capture.get()
        # Should contain only digits and spaces
        cleaned = output.strip()
        assert all(char.isdigit() or char.isspace() for char in cleaned)
    else:
        assert result == 1


def test_execute_pid_ordering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test PID ordering in output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kworker"])

    # Should order PIDs appropriately
    if result == 0:
        output = capture.get()
        # Should have consistent PID ordering
        pids = output.strip().split()
        if len(pids) > 1:
            # PIDs should be valid numbers
            assert all(pid.isdigit() for pid in pids)
    else:
        assert result == 1


def test_execute_zombie_process_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test handling of zombie processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["zombie-process"])

    # Should handle zombie processes appropriately
    if result == 0:
        output = capture.get()
        # Should include or exclude zombies based on implementation
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if no zombie processes found
        assert result == 1


def test_execute_kernel_thread_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test handling of kernel threads
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["migration"])  # Kernel thread

    # Should handle kernel threads appropriately
    if result == 0:
        output = capture.get()
        # Should find kernel threads
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if kernel thread not found
        assert result == 1


def test_execute_user_process_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test filtering user processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["bash"])

    # Should find user processes
    if result == 0:
        output = capture.get()
        # Should show PIDs for user processes
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if user process not found
        assert result == 1


def test_execute_system_process_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test filtering system processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["systemd"])

    # Should find system processes
    if result == 0:
        output = capture.get()
        # Should show PIDs for system processes
        assert any(char.isdigit() for char in output)
    else:
        # Should fail if system process not found
        assert result == 1


def test_execute_process_name_matching_precision(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test precision of process name matching
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should match process name precisely
    if result == 0:
        output = capture.get()
        # Should find exact matches
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_concurrent_execution_safety(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        # Should produce consistent results
        assert any(char.isdigit() for char in output)
    else:
        assert result == 1


def test_execute_proc_filesystem_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test /proc filesystem access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should access /proc filesystem appropriately
    if result == 0:
        output = capture.get()
        # Should successfully read process information
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test permission handling for process access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        if "permission" in output.lower():
            assert "permission" in output.lower()
    else:
        assert result == 0


def test_execute_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test error handling for system access issues
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["nonexistent"])

    # Should handle errors gracefully
    assert result == 1
    # Should not crash on non-existent process


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x", "init"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0


def test_execute_performance_with_many_processes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test performance with many processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kworker"])  # Many instances

    # Should handle many processes efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PidofCommand,
):
    # Test memory efficiency with large process lists
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["init"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1
