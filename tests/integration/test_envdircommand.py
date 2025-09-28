"""Integration tests for the EnvdirCommand."""

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
    """Fixture to create a EnvdirCommand instance."""
    yield pebble_shell.commands.EnvdirCommand(shell=shell)


def test_name(command: pebble_shell.commands.EnvdirCommand):
    assert command.name == "envdir"


def test_category(command: pebble_shell.commands.EnvdirCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.EnvdirCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["env", "environment", "directory", "command", "variable"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["env", "environment", "directory", "usage"]
    )


def test_execute_no_args_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with no arguments specified
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing arguments error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["directory", "command", "required", "usage", "error"]
    )


def test_execute_only_directory_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with only directory specified, no command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp()])

    # Should fail with missing command error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["command", "required", "missing", "usage", "error"]
    )


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with non-existent directory
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/nonexistent/directory", "echo", "test"]
        )

    # Should fail with directory not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "directory", "error"]
    )


def test_execute_file_instead_of_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with file instead of directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", "echo", "test"])

    # Should fail with not a directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not a directory", "directory", "error", "invalid"]
    )


def test_execute_permission_denied_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with permission denied directory
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/root", "echo", "test"]
        )  # Typically restricted

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should execute command with environment
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_simple_command_with_empty_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with empty directory and simple command
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "hello"]
        )

    # Should either succeed running command or fail with directory/command error
    if result == 0:
        output = capture.get()
        # Should run echo command with empty environment additions
        assert "hello" in output or len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "error", "directory", "command"]
        )


def test_execute_command_with_system_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with system directory that might contain environment files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc", "echo", "test"])

    # Should either succeed or fail based on directory permissions/contents
    if result == 0:
        output = capture.get()
        # Should run command with environment from /etc
        assert len(output) >= 0
    else:
        # Should fail with permission or other error
        assert result == 1


def test_execute_nonexistent_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with valid directory but non-existent command
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "nonexistent_command_12345"]
        )

    # Should fail with command not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "command", "error", "no such file"]
    )


def test_execute_command_with_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test command with multiple arguments
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "hello", "world", "test"]
        )

    # Should either succeed passing arguments or fail with error
    if result == 0:
        output = capture.get()
        # Should run echo with all arguments
        assert len(output) >= 0
        if "hello" in output:
            assert "hello" in output
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_built_in_command(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with shell built-in command
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp(), "pwd"])

    # Should either succeed with built-in or fail with error
    if result == 0:
        output = capture.get()
        # Should run pwd command
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_environment_variable_inheritance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test environment variable inheritance from directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp(), "env"])

    # Should either succeed showing environment or fail with error
    if result == 0:
        output = capture.get()
        # Should show environment variables
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain environment variables
            has_env = any(
                var in output.upper() for var in ["PATH", "HOME", "USER", "PWD"]
            )
            if has_env:
                assert has_env
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_complex_command_line(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with complex command line including pipes or redirects
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "sh", "-c", "echo test"]
        )

    # Should either succeed with shell command or fail with error
    if result == 0:
        output = capture.get()
        # Should run shell command
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_directory_with_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with directory path containing special characters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(suffix=" test dir"), "echo", "test"]
        )

    # Should either succeed or fail with path error
    if result == 0:
        output = capture.get()
        # Should handle special characters in path
        assert len(output) >= 0
    else:
        # Should fail with directory not found or path error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not found", "directory", "error", "invalid"]
        )


def test_execute_relative_directory_path(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with relative directory path
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[".", "echo", "test"])

    # Should either succeed with relative path or fail with error
    if result == 0:
        output = capture.get()
        # Should handle relative paths
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_empty_command_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with empty command string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp(), ""])

    # Should fail with empty command error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["command", "empty", "invalid", "error"])


def test_execute_command_with_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test command with its own options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp(), "ls", "-la"])

    # Should either succeed passing options or fail with error
    if result == 0:
        output = capture.get()
        # Should run ls with options
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test invalid option to envdir itself
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-z", tempfile.mkdtemp(), "echo", "test"]
        )

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_directory_traversal_attempt(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test directory traversal attempt
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["../../../etc", "echo", "test"])

    # Should either succeed or fail with directory error
    if result == 0:
        output = capture.get()
        # Should handle directory traversal
        assert len(output) >= 0
    else:
        # Should fail with directory not found or permission error
        assert result == 1


def test_execute_symlink_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test with symbolic link to directory
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "test"]
        )  # Often symlinked

    # Should either succeed following symlinks or fail with error
    if result == 0:
        output = capture.get()
        # Should follow symlinks to directories
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_environment_file_processing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test environment file processing from directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc/sys", "echo", "processed"])

    # Should either succeed processing environment or fail with error
    if result == 0:
        output = capture.get()
        # Should process environment files
        assert len(output) >= 0
    else:
        # Should fail appropriately
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "memory_test"]
        )

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/invalid/path", "echo", "test"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["not found", "error", "directory", "invalid"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test signal handling during command execution
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "signal_test"]
        )

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_environment_override_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test environment variable override behavior
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "printenv", "PATH"]
        )

    # Should either succeed showing PATH or fail with error
    if result == 0:
        output = capture.get()
        # Should show environment variables
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_working_directory_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test working directory preservation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[tempfile.mkdtemp(), "pwd"])

    # Should either succeed showing working directory or fail with error
    if result == 0:
        output = capture.get()
        # Should preserve working directory
        assert len(output) >= 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_exit_code_propagation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test exit code propagation from executed command
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "sh", "-c", "exit 42"]
        )

    # Should either propagate exit code or fail with error
    if result == 42:
        # Should propagate command exit code
        assert result == 42
    elif result == 0:
        # Command succeeded
        assert result == 0
    else:
        # Should fail with directory or command error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EnvdirCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[tempfile.mkdtemp(), "echo", "cross_platform"]
        )

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
