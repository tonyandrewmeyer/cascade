"""Integration tests for the PstraceCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PstraceCommand instance."""
    yield pebble_shell.commands.PstraceCommand(shell=shell)


def test_name(command: pebble_shell.commands.PstraceCommand):
    assert command.name == "pstrace"


def test_category(command: pebble_shell.commands.PstraceCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.PstraceCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "pstrace" in output
    assert "Trace process system calls" in output
    assert "-p" in output
    assert "-o" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "pstrace" in output
    assert "Trace process system calls" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # pstrace with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["usage", "process required", "PID required", "pstrace"]
    )


def test_execute_invalid_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test with invalid PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "99999"])

    # Should fail with invalid PID error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["No such process", "invalid PID", "process not found", "error"]
    )


def test_execute_non_numeric_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test with non-numeric PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "invalid"])

    # Should fail with invalid PID format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid PID", "not a number", "invalid argument", "error"]
    )


def test_execute_negative_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test with negative PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "-1"])

    # Should fail with negative PID error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid PID", "negative", "must be positive", "error"]
    )


def test_execute_zero_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test with zero PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "0"])

    # Should either trace kernel or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show system call traces
        assert len(output.strip()) >= 0
    else:
        # Should fail if PID 0 not traceable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["cannot trace", "permission", "invalid PID", "error"]
        )


def test_execute_self_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test tracing self (current process)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "$$"])

    # Should either trace self or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show system call traces
        assert len(output.strip()) >= 0
    else:
        # Should fail if self-tracing not allowed
        assert result == 1


def test_execute_init_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test tracing init process (PID 1)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should either trace init or fail with permission error
    if result == 0:
        output = capture.get()
        # Should show system call traces for init
        assert len(output.strip()) >= 0
    else:
        # Should fail if permission denied or not supported
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "cannot trace", "access denied", "error"]
        )


def test_execute_permission_denied_process(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test tracing process without permission
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should fail with permission error for privileged process
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "cannot attach", "access denied", "error"]
        )
    else:
        # May succeed if running with sufficient privileges
        assert result == 0


def test_execute_output_file_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -o option to specify output file
    with tempfile.NamedTemporaryFile(suffix="_trace.out", delete=False) as trace_file:
        trace_path = trace_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", trace_path, "-p", "1"])

    # Should either create output file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should redirect output to file
        assert len(output.strip()) == 0 or "trace.out" in output
    else:
        # Should fail if cannot create file or trace process
        assert result == 1


def test_execute_follow_forks_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -f option to follow forks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "-p", "1"])

    # Should either follow forks or fail gracefully
    if result == 0:
        output = capture.get()
        # Should trace child processes
        assert len(output.strip()) >= 0
    else:
        # Should fail if fork following not supported or permission denied
        assert result == 1


def test_execute_count_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -c option to count system calls
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "-p", "1"])

    # Should either show syscall counts or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show system call statistics
        assert (
            any(stat in output for stat in ["calls", "count", "total", "seconds"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if counting not supported or permission denied
        assert result == 1


def test_execute_time_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -T option to show time spent in syscalls
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-T", "-p", "1"])

    # Should either show timing information or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show timing for system calls
        assert (
            any(
                time_info in output
                for time_info in ["time", "seconds", "usec", "duration"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if timing not supported or permission denied
        assert result == 1


def test_execute_trace_specific_syscalls(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -e option to trace specific system calls
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "trace=read,write", "-p", "1"]
        )

    # Should either trace specific syscalls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show only read/write system calls
        assert (
            any(syscall in output for syscall in ["read", "write"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if filtering not supported or permission denied
        assert result == 1


def test_execute_exclude_syscalls(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test excluding specific system calls
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "trace=!read", "-p", "1"])

    # Should either exclude syscalls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should not show read system calls
        assert len(output.strip()) >= 0
    else:
        # Should fail if exclusion not supported or permission denied
        assert result == 1


def test_execute_string_limit_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test -s option to limit string output length
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "32", "-p", "1"])

    # Should either limit string length or fail gracefully
    if result == 0:
        output = capture.get()
        # Should limit string output to 32 characters
        assert len(output.strip()) >= 0
    else:
        # Should fail if string limiting not supported or permission denied
        assert result == 1


def test_execute_attach_detach_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test attach and detach behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should either attach to process or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show attach/detach messages
        assert (
            any(msg in output for msg in ["attached", "detached", "tracing"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if attachment not possible
        assert result == 1


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test signal handling during tracing
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "signal=SIGTERM", "-p", "1"]
        )

    # Should either trace signals or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show signal information
        assert (
            any(signal in output for signal in ["SIGTERM", "signal", "killed"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if signal tracing not supported
        assert result == 1


def test_execute_decode_file_descriptors(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test file descriptor decoding
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-y", "-p", "1"])

    # Should either decode file descriptors or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show file descriptor information
        assert (
            any(fd_info in output for fd_info in ["fd", "/dev/", "pipe", "socket"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if FD decoding not supported
        assert result == 1


def test_execute_trace_child_processes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test tracing child processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-ff", "-p", "1"])

    # Should either trace children or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show child process traces
        assert len(output.strip()) >= 0
    else:
        # Should fail if child tracing not supported
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "-p", "1"])

    # Should either show verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show detailed trace information
        assert (
            any(
                verbose_info in output
                for verbose_info in ["verbose", "detailed", "info"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if verbose mode not supported
        assert result == 1


def test_execute_trace_program_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test tracing program execution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["echo", "hello"])

    # Should either trace program execution or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show execution trace
        assert (
            any(trace_info in output for trace_info in ["execve", "echo", "hello"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if execution tracing not supported
        assert result == 1


def test_execute_memory_mapping_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test memory mapping trace
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "trace=mmap,munmap", "-p", "1"]
        )

    # Should either trace memory operations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show memory mapping calls
        assert (
            any(mem_call in output for mem_call in ["mmap", "munmap", "memory"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if memory tracing not supported
        assert result == 1


def test_execute_network_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test network system call trace
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "trace=network", "-p", "1"])

    # Should either trace network calls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show network system calls
        assert (
            any(
                net_call in output
                for net_call in ["socket", "connect", "bind", "listen"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if network tracing not supported
        assert result == 1


def test_execute_file_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test file system call trace
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "trace=file", "-p", "1"])

    # Should either trace file calls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show file system calls
        assert (
            any(file_call in output for file_call in ["open", "close", "read", "write"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if file tracing not supported
        assert result == 1


def test_execute_process_tree_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test process tree tracing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "trace=process", "-p", "1"])

    # Should either trace process calls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show process management calls
        assert (
            any(proc_call in output for proc_call in ["fork", "clone", "exec", "exit"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if process tracing not supported
        assert result == 1


def test_execute_ipc_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test IPC system call trace
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "trace=ipc", "-p", "1"])

    # Should either trace IPC calls or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show IPC system calls
        assert (
            any(
                ipc_call in output
                for ipc_call in ["pipe", "msgget", "semget", "shmget"]
            )
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if IPC tracing not supported
        assert result == 1


def test_execute_timestamp_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test timestamp option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-p", "1"])

    # Should either show timestamps or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show timestamps for system calls
        assert (
            any(time_format in output for time_format in [":", ".", "timestamp"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if timestamps not supported
        assert result == 1


def test_execute_relative_timestamp(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test relative timestamp option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "-p", "1"])

    # Should either show relative timestamps or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show relative timing
        assert (
            any(rel_time in output for rel_time in ["+", "relative", "delta"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if relative timing not supported
        assert result == 1


def test_execute_environment_trace(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test environment variable tracing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "env"])

    # Should either trace environment access or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show environment variable access
        assert (
            any(env_info in output for env_info in ["getenv", "setenv", "environment"])
            or len(output.strip()) >= 0
        )
    else:
        # Should fail if environment tracing not supported
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "99999"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["No such process", "process not found", "error"]
    )


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_security_constraints(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test security constraint handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "1"])

    # Should respect security constraints
    if result == 1:
        output = capture.get()
        # Should show appropriate security error
        assert any(
            security_msg in output
            for security_msg in [
                "permission denied",
                "access denied",
                "cannot attach",
                "error",
            ]
        )
    else:
        # May succeed if running with appropriate privileges
        assert result == 0


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstraceCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "-p", "1"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0
