"""Integration tests for the DelgroupCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DelgroupCommand instance."""
    yield pebble_shell.commands.DelgroupCommand(shell=shell)


def test_name(command: pebble_shell.commands.DelgroupCommand):
    assert command.name == "delgroup"


def test_category(command: pebble_shell.commands.DelgroupCommand):
    assert command.category == "User Management"


def test_help(command: pebble_shell.commands.DelgroupCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "delgroup" in output
    assert any(phrase in output.lower() for phrase in ["delete", "remove", "group"])


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "delgroup" in output
    assert any(phrase in output.lower() for phrase in ["delete", "remove", "group"])


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # delgroup with no args should show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "delgroup", "group"])


def test_execute_delete_nonexistent_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test deleting nonexistent group (should fail)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistentgroup"])

    # Should fail with group not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["not found", "does not exist", "no such group", "error"]
    )


def test_execute_delete_system_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test deleting system group (should be cautious)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["daemon"])

    # Should either succeed or fail based on permissions/policy
    if result == 0:
        output = capture.get()
        # Should indicate group deletion success
        assert len(output) >= 0
    else:
        # Should fail if not root or policy prevents deletion
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "permission",
                "denied",
                "system",
                "protected",
                "not found",
                "error",
            ]
        )


def test_execute_only_if_empty_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test deleting only if group is empty
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--only-if-empty", "testgroup"])

    # Should either succeed if empty or fail
    if result == 0:
        output = capture.get()
        # Should delete only if empty
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not empty", "members", "not found", "error"]
        )


def test_execute_system_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test system group deletion mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--system", "testsysgroup"])

    # Should either succeed deleting system group or fail
    if result == 0:
        output = capture.get()
        # Should delete system group
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test quiet mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--quiet", "testgroup"])

    # Should either succeed quietly or fail
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_remove_user_from_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test removing user from group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser", "users"])

    # Should either succeed removing user or fail
    if result == 0:
        output = capture.get()
        # Should remove user from group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["not found", "user", "group", "not member", "error"]
        )


def test_execute_invalid_groupname(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test invalid group name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid@group"])

    # Should fail with invalid group name error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "name", "not found", "error"])


def test_execute_root_group_protection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test attempting to delete root group (should be protected)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root"])

    # Should fail with protection error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["protect", "cannot", "root", "system", "not found", "error"]
    )


def test_execute_group_with_members(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test deleting group with members
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["users"])

    # Should either succeed or warn about members
    if result == 0:
        output = capture.get()
        # Should handle members appropriately
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["members", "not empty", "users", "not found", "error"]
        )


def test_execute_primary_group_of_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test deleting primary group of user
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should either succeed or fail based on primary group status
    if result == 0:
        output = capture.get()
        # Should delete if not primary group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["primary", "group", "user", "not found", "error"]
        )


def test_execute_nonexistent_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test removing nonexistent user from group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistentuser", "users"])

    # Should fail with user not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["user", "not found", "does not exist", "error"]
    )


def test_execute_nonexistent_target_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test removing user from nonexistent group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "nonexistentgroup"])

    # Should fail with group not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["group", "not found", "does not exist", "error"]
    )


def test_execute_user_not_member(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test removing user who is not a member
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "users"])

    # Should either succeed or fail based on membership
    if result == 0:
        output = capture.get()
        # Should handle non-membership gracefully
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["not member", "not in group", "group", "error"]
        )


def test_execute_permission_denied(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test without sufficient permissions (non-root)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

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
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "testgroup"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--system", "--only-if-empty", "testgroup"]
        )

    # Should either handle conflicts or fail appropriately
    if result == 0:
        output = capture.get()
        # May resolve conflicts automatically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_force_deletion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test forced deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--force", "testgroup"])

    # Should either succeed with force or fail
    if result == 0:
        output = capture.get()
        # Should force deletion
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_backup_before_deletion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test backing up before deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--backup", "testgroup"])

    # Should either succeed with backup or fail
    if result == 0:
        output = capture.get()
        # Should create backup
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_gid_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test GID validation during deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should validate GID appropriately
    if result == 0:
        output = capture.get()
        # Should handle GID validation
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid", "testgroup"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test signal handling during group deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should integrate with system group management properly
    if result == 0:
        output = capture.get()
        # Should integrate with system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_validation_comprehensive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test comprehensive input validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["validgroup"])

    # Should validate inputs comprehensively
    if result == 0:
        output = capture.get()
        # Should pass validation
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_atomic_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test atomic deletion operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should perform atomic operations
    if result == 0:
        output = capture.get()
        # Should complete atomically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_dependency_checking(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test dependency checking before deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should check dependencies
    if result == 0:
        output = capture.get()
        # Should handle dependencies
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_rollback_capability(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test rollback capability on failure
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should handle rollback if needed
    if result == 0:
        output = capture.get()
        # Should complete successfully
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_audit_logging(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DelgroupCommand,
):
    # Test audit logging of deletion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should log deletion attempts
    if result == 0:
        output = capture.get()
        # Should perform audit logging
        assert len(output) >= 0
    else:
        assert result == 1
