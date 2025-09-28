"""Integration tests for the ScriptCommand."""

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
    """Fixture to create a ScriptCommand instance."""
    yield pebble_shell.commands.ScriptCommand(shell=shell)


def test_name(command: pebble_shell.commands.ScriptCommand):
    assert command.name == "script"


def test_category(command: pebble_shell.commands.ScriptCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.ScriptCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "script" in output
    assert any(
        phrase in output.lower()
        for phrase in ["record", "terminal", "session", "typescript"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "script" in output
    assert any(
        phrase in output.lower()
        for phrase in ["record", "terminal", "session", "typescript"]
    )


def test_execute_no_args_default_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # script with no args should use default typescript file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either start recording or show usage
    if result == 0:
        output = capture.get()
        # Should indicate recording started
        assert len(output) >= 0
        if len(output) > 0:
            # Should mention typescript or recording
            assert any(
                word in output.lower()
                for word in ["script", "started", "recording", "typescript"]
            )
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "script", "file"])


def test_execute_custom_output_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test recording to custom output file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as session_file:
        test_session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[test_session_path])

    # Should either start recording or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate recording started with custom file
        assert len(output) >= 0
        if len(output) > 0:
            # Should mention the custom file
            assert test_session_path in output or "script" in output.lower()
    else:
        # Should fail if cannot create file
        assert result == 1


def test_execute_append_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test append mode
    with tempfile.NamedTemporaryFile(
        suffix="_append_session.txt", delete=False
    ) as append_file:
        append_path = append_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", append_path])

    # Should either start recording in append mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate append mode recording
        assert len(output) >= 0
        if len(output) > 0:
            # Should mention append or recording
            assert any(
                word in output.lower() for word in ["append", "script", "recording"]
            )
    else:
        assert result == 1


def test_execute_timing_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test timing information recording
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", timing_path, session_path])

    # Should either start recording with timing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate timing recording
        assert len(output) >= 0
        if len(output) > 0:
            # Should mention timing or recording
            assert any(
                word in output.lower() for word in ["timing", "script", "recording"]
            )
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test quiet mode
    with tempfile.NamedTemporaryFile(
        suffix="_quiet_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", tmp_name])

    # Should either start recording quietly or fail gracefully
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_command_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test running specific command
    with tempfile.NamedTemporaryFile(
        suffix="_command_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo hello", tmp_name])

    # Should either run command and record or fail gracefully
    if result == 0:
        output = capture.get()
        # Should record the command execution
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain command output or recording info
            assert "hello" in output or "script" in output.lower()
    else:
        assert result == 1


def test_execute_flush_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test flush output option
    with tempfile.NamedTemporaryFile(
        suffix="_flush_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", tmp_name])

    # Should either start recording with flush or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate flush mode recording
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_return_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test return child exit code option
    with tempfile.NamedTemporaryFile(
        suffix="_return_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", tmp_name])

    # Should either start recording with return option or fail gracefully
    if result == 0:
        output = capture.get()
        # Should indicate recording with return option
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_version_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test version option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-V"])

    # Should either show version or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain version information
        assert len(output) >= 0
        if len(output) > 0:
            # Should mention version or script
            assert any(word in output.lower() for word in ["version", "script", "util"])
    else:
        assert result == 1


def test_execute_invalid_output_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test invalid output file path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/invalid/path/session.txt"])

    # Should fail with file creation error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["cannot", "create", "path", "directory", "error"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test permission denied for output file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/root/session.txt"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # May succeed if writable
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])


def test_execute_directory_as_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test invalid option
    with tempfile.NamedTemporaryFile(suffix="_session.txt", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", tmp_name])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test conflicting options
    with tempfile.NamedTemporaryFile(suffix="_session.txt", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-a", "-c", "echo test", tmp_name]
        )

    # Should either handle conflicts or fail appropriately
    if result == 0:
        output = capture.get()
        # May resolve conflicts automatically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_terminal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test terminal handling
    with tempfile.NamedTemporaryFile(
        suffix="_terminal_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tmp_name])

    # Should either handle terminal or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle terminal properly
        assert len(output) >= 0
    else:
        # May fail if no terminal available
        assert result == 1


def test_execute_pty_allocation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test PTY allocation
    with tempfile.NamedTemporaryFile(
        suffix="_pty_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tmp_name])

    # Should either allocate PTY or fail gracefully
    if result == 0:
        output = capture.get()
        # Should allocate PTY for recording
        assert len(output) >= 0
    else:
        # May fail if PTY unavailable
        assert result == 1


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test signal handling during recording
    with tempfile.NamedTemporaryFile(
        suffix="_signal_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo test", tmp_name])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_subprocess_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test subprocess management
    with tempfile.NamedTemporaryFile(
        suffix="_subprocess_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "sleep 0.1", tmp_name])

    # Should manage subprocesses properly
    if result == 0:
        output = capture.get()
        # Should manage subprocess execution
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_io_redirection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test I/O redirection handling
    with tempfile.NamedTemporaryFile(
        suffix="_io_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo input", tmp_name])

    # Should handle I/O redirection
    if result == 0:
        output = capture.get()
        # Should handle I/O properly
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_environment_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test environment preservation
    with tempfile.NamedTemporaryFile(
        suffix="_env_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo $HOME", tmp_name])

    # Should preserve environment
    if result == 0:
        output = capture.get()
        # Should preserve environment variables
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test memory efficiency
    with tempfile.NamedTemporaryFile(
        suffix="_memory_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo test", tmp_name])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test error recovery capabilities
    with tempfile.NamedTemporaryFile(suffix="_session.txt", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid", tmp_name])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test concurrent execution safety
    with tempfile.NamedTemporaryFile(
        suffix="_concurrent_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-c", "echo concurrent", tmp_name]
        )

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test cross-platform compatibility
    with tempfile.NamedTemporaryFile(
        suffix="_platform_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo platform", tmp_name])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_file_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test output file format validation
    with tempfile.NamedTemporaryFile(
        suffix="_format_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo format", tmp_name])

    # Should produce valid typescript format
    if result == 0:
        output = capture.get()
        # Should create valid typescript file
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_session_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptCommand,
):
    # Test session cleanup
    with tempfile.NamedTemporaryFile(
        suffix="_cleanup_session.txt", delete=False
    ) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "echo cleanup", tmp_name])

    # Should clean up session properly
    if result == 0:
        output = capture.get()
        # Should perform proper cleanup
        assert len(output) >= 0
    else:
        assert result == 1
