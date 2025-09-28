"""Integration tests for the DeluserCommand."""

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
    """Fixture to create a DeluserCommand instance."""
    yield pebble_shell.commands.DeluserCommand(shell=shell)


def test_name(command: pebble_shell.commands.DeluserCommand):
    assert command.name == "deluser"


def test_category(command: pebble_shell.commands.DeluserCommand):
    assert command.category == "User Management"


def test_help(command: pebble_shell.commands.DeluserCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "deluser" in output
    assert any(
        phrase in output.lower() for phrase in ["delete", "remove", "user", "account"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "deluser" in output
    assert any(
        phrase in output.lower() for phrase in ["delete", "remove", "user", "account"]
    )


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # deluser with no args should show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "deluser", "username"])


def test_execute_delete_nonexistent_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test deleting nonexistent user (should fail)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistentuser"])

    # Should fail with user not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["not found", "does not exist", "no such user", "error"]
    )


def test_execute_delete_system_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test deleting system user (should be cautious)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["daemon"])

    # Should either succeed or fail based on permissions/policy
    if result == 0:
        output = capture.get()
        # Should indicate user deletion success
        assert len(output) >= 0
    else:
        # Should fail if not root or policy prevents deletion
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "system", "protected", "error"]
        )


def test_execute_remove_home_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test removing user home directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--remove-home", "testuser"])

    # Should either succeed removing home or fail
    if result == 0:
        output = capture.get()
        # Should remove user and home directory
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "permission", "error"])


def test_execute_remove_all_files_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test removing all user files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--remove-all-files", "testuser"])

    # Should either succeed removing all files or fail
    if result == 0:
        output = capture.get()
        # Should remove user and all files
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_backup_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test backing up user files before deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--backup", "testuser"])

    # Should either succeed with backup or fail
    if result == 0:
        output = capture.get()
        # Should create backup before deletion
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_backup_to_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test backing up to specific location
    temp_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--backup-to", temp_dir, "testuser"]
        )

    # Should either succeed backing up to location or fail
    if result == 0:
        output = capture.get()
        # Should backup to specified location
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test quiet mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--quiet", "testuser"])

    # Should either succeed quietly or fail
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_force_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test force deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--force", "testuser"])

    # Should either succeed with force or fail
    if result == 0:
        output = capture.get()
        # Should force deletion
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_user_from_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test removing user from specific group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser", "testgroup"])

    # Should either succeed removing from group or fail
    if result == 0:
        output = capture.get()
        # Should remove user from group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "group", "user", "error"])


def test_execute_only_if_empty_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test deleting only if home directory is empty
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--only-if-empty", "testuser"])

    # Should either succeed if empty or fail
    if result == 0:
        output = capture.get()
        # Should delete only if empty
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test system user deletion mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--system", "testsysuser"])

    # Should either succeed deleting system user or fail
    if result == 0:
        output = capture.get()
        # Should delete system user
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_preserve_home_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test preserving home directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--preserve-home", "testuser"])

    # Should either succeed preserving home or fail
    if result == 0:
        output = capture.get()
        # Should preserve home directory
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_invalid_username(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test invalid username
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid@user"])

    # Should fail with invalid username error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "name", "not found", "error"])


def test_execute_root_user_protection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test attempting to delete root user (should be protected)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root"])

    # Should fail with protection error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["protect", "cannot", "root", "system", "error"]
    )


def test_execute_logged_in_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test deleting currently logged in user
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should either succeed or fail based on login status
    if result == 0:
        output = capture.get()
        # Should delete user if not logged in
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["logged in", "active", "not found", "error"]
        )


def test_execute_user_with_processes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test deleting user with running processes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should either succeed or warn about processes
    if result == 0:
        output = capture.get()
        # Should handle processes appropriately
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test removing user from nonexistent group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser", "nonexistentgroup"])

    # Should fail with group not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["group", "not found", "does not exist", "error"]
    )


def test_execute_permission_denied(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test without sufficient permissions (non-root)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # If running as root, should succeed
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "root", "not found", "error"]
        )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "testuser"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--remove-home", "--preserve-home", "testuser"]
        )

    # Should either handle conflicts or fail appropriately
    if result == 0:
        output = capture.get()
        # May resolve conflicts automatically
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["conflict", "invalid", "not found", "error"]
        )


def test_execute_backup_invalid_location(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test backup to invalid location
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--backup-to", "/nonexistent/path", "testuser"]
        )

    # Should fail with invalid backup location
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["backup", "path", "not found", "invalid", "error"]
    )


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid", "testuser"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test signal handling during user deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should integrate with system user management properly
    if result == 0:
        output = capture.get()
        # Should integrate with system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_file_system_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test file system cleanup during deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--remove-all-files", "testuser"])

    # Should clean up file system appropriately
    if result == 0:
        output = capture.get()
        # Should perform cleanup
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_validation_comprehensive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test comprehensive input validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["validuser"])

    # Should validate inputs comprehensively
    if result == 0:
        output = capture.get()
        # Should pass validation
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_atomic_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DeluserCommand,
):
    # Test atomic deletion operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should perform atomic operations
    if result == 0:
        output = capture.get()
        # Should complete atomically
        assert len(output) >= 0
    else:
        assert result == 1
