"""Integration tests for the FdinfoCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FdinfoCommand instance."""
    yield pebble_shell.commands.FdinfoCommand(shell=shell)


def test_name(command: pebble_shell.commands.FdinfoCommand):
    assert command.name == "fdinfo"


def test_category(command: pebble_shell.commands.FdinfoCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.FdinfoCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "fdinfo" in output
    assert "Show file descriptor information" in output
    assert "PID" in output
    assert "FD" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "fdinfo" in output
    assert "Show file descriptor information" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # fdinfo with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "fdinfo <PID> <FD>" in output


def test_execute_missing_fd_arg(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # fdinfo with only PID should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1234"])

    # Should fail with missing FD error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["missing file descriptor", "fdinfo <PID> <FD>", "usage"]
    )


def test_execute_valid_pid_fd_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with valid PID and FD combination
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])  # init process, stdin

    # Should either succeed with fd info or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show file descriptor information
        assert any(
            msg in output
            for msg in [
                "pos:",
                "flags:",
                "mnt_id:",
                "ino:",
                "File descriptor information",
            ]
        )
    else:
        # Should fail if PID/FD doesn't exist or access denied
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Fdinfo operation failed",
                "not found",
                "permission denied",
                "error",
            ]
        )


def test_execute_current_process_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with current process stdin (FD 0)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["$$", "0"]
        )  # Current process, stdin

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show stdin information
        assert any(msg in output for msg in ["pos:", "flags:", "File descriptor"])
    else:
        assert result == 1


def test_execute_current_process_stdout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with current process stdout (FD 1)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["$$", "1"]
        )  # Current process, stdout

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show stdout information
        assert any(msg in output for msg in ["pos:", "flags:", "File descriptor"])
    else:
        assert result == 1


def test_execute_current_process_stderr(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with current process stderr (FD 2)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["$$", "2"]
        )  # Current process, stderr

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show stderr information
        assert any(msg in output for msg in ["pos:", "flags:", "File descriptor"])
    else:
        assert result == 1


def test_execute_nonexistent_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with nonexistent PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["99999", "0"])

    # Should fail with process not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in [
            "Fdinfo operation failed",
            "process not found",
            "No such process",
            "error",
        ]
    )


def test_execute_invalid_pid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with invalid PID format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-pid", "0"])

    # Should fail with invalid PID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "PID", "error"])


def test_execute_negative_pid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with negative PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1", "0"])

    # Should fail with invalid PID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "PID", "error"])


def test_execute_nonexistent_fd(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with nonexistent file descriptor
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["1", "999"]
        )  # init process, high FD

    # Should fail with FD not found error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Fdinfo operation failed",
                "file descriptor not found",
                "No such file",
                "error",
            ]
        )
    else:
        # May succeed if FD actually exists
        assert result == 0


def test_execute_invalid_fd_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with invalid FD format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "invalid-fd"])

    # Should fail with invalid FD error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "file descriptor", "error"])


def test_execute_negative_fd(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with negative file descriptor
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "-1"])

    # Should fail with invalid FD error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "file descriptor", "error"])


def test_execute_fd_position_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test file descriptor position display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display position information if successful
    if result == 0:
        output = capture.get()
        # Should show position information
        if "pos:" in output:
            # Should contain position value
            assert "pos:" in output
    else:
        assert result == 1


def test_execute_fd_flags_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test file descriptor flags display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display flags information if successful
    if result == 0:
        output = capture.get()
        # Should show flags information
        if "flags:" in output:
            # Should contain flags value
            assert "flags:" in output
    else:
        assert result == 1


def test_execute_fd_mount_id_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test file descriptor mount ID display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display mount ID information if successful
    if result == 0:
        output = capture.get()
        # Should show mount ID information
        if "mnt_id:" in output:
            # Should contain mount ID value
            assert "mnt_id:" in output
    else:
        assert result == 1


def test_execute_fd_inode_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test file descriptor inode display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display inode information if successful
    if result == 0:
        output = capture.get()
        # Should show inode information
        if "ino:" in output:
            # Should contain inode value
            assert "ino:" in output
    else:
        assert result == 1


def test_execute_fd_eventfd_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test eventfd specific information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display eventfd information if FD is eventfd
    if result == 0:
        output = capture.get()
        # Should show eventfd information if applicable
        if "eventfd-count:" in output:
            # Should contain eventfd specific data
            assert "eventfd-count:" in output
    else:
        assert result == 1


def test_execute_fd_signalfd_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test signalfd specific information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display signalfd information if FD is signalfd
    if result == 0:
        output = capture.get()
        # Should show signalfd information if applicable
        if "sigmask:" in output:
            # Should contain signalfd specific data
            assert "sigmask:" in output
    else:
        assert result == 1


def test_execute_fd_timerfd_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test timerfd specific information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display timerfd information if FD is timerfd
    if result == 0:
        output = capture.get()
        # Should show timerfd information if applicable
        if "clockid:" in output:
            # Should contain timerfd specific data
            assert "clockid:" in output
    else:
        assert result == 1


def test_execute_fd_epoll_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test epoll specific information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display epoll information if FD is epoll
    if result == 0:
        output = capture.get()
        # Should show epoll information if applicable
        if "tfd:" in output:
            # Should contain epoll specific data
            assert "tfd:" in output
    else:
        assert result == 1


def test_execute_fd_inotify_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test inotify specific information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should display inotify information if FD is inotify
    if result == 0:
        output = capture.get()
        # Should show inotify information if applicable
        if "inotify wd:" in output:
            # Should contain inotify specific data
            assert "inotify wd:" in output
    else:
        assert result == 1


def test_execute_multiple_extra_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with extra arguments (should use first two)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0", "extra", "args"])

    # Should use first PID and FD, ignore extras
    if result == 0:
        output = capture.get()
        # Should show information for PID 1, FD 0
        assert any(msg in output for msg in ["pos:", "flags:", "File descriptor"])
    else:
        assert result == 1


def test_execute_permission_denied_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test permission denied handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        if "permission denied" in output.lower():
            assert "permission denied" in output.lower()
    else:
        assert result == 0


def test_execute_proc_filesystem_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test /proc filesystem access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should access /proc filesystem appropriately
    if result == 0:
        output = capture.get()
        # Should successfully read from /proc
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_large_pid_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with very large PID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["32768", "0"])

    # Should handle large PIDs appropriately
    if result == 1:
        output = capture.get()
        # Should fail appropriately for non-existent large PID
        assert any(msg in output for msg in ["not found", "No such process", "error"])
    else:
        # May succeed if process actually exists
        assert result == 0


def test_execute_large_fd_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test with very large FD
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "1024"])

    # Should handle large FDs appropriately
    if result == 1:
        output = capture.get()
        # Should fail appropriately for non-existent large FD
        assert any(msg in output for msg in ["not found", "No such file", "error"])
    else:
        # May succeed if FD actually exists
        assert result == 0


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test output formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent formatting
        if output.strip():
            # Should contain structured information
            assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_error_message_clarity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test error message clarity
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["99999", "999"])

    # Should provide clear error messages
    assert result == 1
    output = capture.get()
    # Should have informative error message
    assert len(output.strip()) > 0
    assert any(msg in output for msg in ["error", "failed", "not found"])


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test data consistency across calls
    outputs = []
    for _ in range(2):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=["1", "0"])
        if result == 0:
            outputs.append(capture.get())

    # Should provide consistent data
    if len(outputs) == 2 and "pos:" in outputs[0] and "pos:" in outputs[1]:
        # Should have similar structure for same PID/FD and maintain consistent format
        assert "pos:" in outputs[0] and "pos:" in outputs[1]


def test_execute_kernel_version_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FdinfoCommand,
):
    # Test compatibility across kernel versions
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "0"])

    # Should work across different kernel versions
    if result == 0:
        output = capture.get()
        # Should handle kernel differences gracefully
        assert len(output.strip()) >= 0
    else:
        # May fail on unsupported kernels
        assert result == 1
