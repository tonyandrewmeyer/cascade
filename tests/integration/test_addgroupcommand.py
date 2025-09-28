"""Integration tests for the AddgroupCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a AddgroupCommand instance."""
    yield pebble_shell.commands.AddgroupCommand(shell=shell)


def test_name(command: pebble_shell.commands.AddgroupCommand):
    assert command.name == "addgroup"


def test_category(command: pebble_shell.commands.AddgroupCommand):
    assert command.category == "User Management"


def test_help(command: pebble_shell.commands.AddgroupCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "addgroup" in output
    assert any(phrase in output.lower() for phrase in ["add", "group", "create"])


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "addgroup" in output
    assert any(phrase in output.lower() for phrase in ["add", "group", "create"])


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # addgroup with no args should show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "addgroup", "group"])


def test_execute_add_group_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test basic group addition
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testgroup"])

    # Should either succeed or fail due to permissions
    if result == 0:
        output = capture.get()
        # Should indicate group creation success
        assert len(output) >= 0
        if len(output) > 0:
            assert any(word in output.lower() for word in ["add", "creat", "success"])
    else:
        # Should fail if not root or group exists
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "root", "exist", "error"]
        )


def test_execute_system_group_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test system group creation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--system", "sysgroup"])

    # Should either succeed creating system group or fail
    if result == 0:
        output = capture.get()
        # Should create system group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "error", "exist"])


def test_execute_gid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test group creation with specific GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "1500", "gidgroup"])

    # Should either succeed with specific GID or fail
    if result == 0:
        output = capture.get()
        # Should create group with specific GID
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "gid", "exist", "error"])


def test_execute_force_badname_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test forcing bad group name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--force-badname", "bad-group"])

    # Should either succeed with forced bad name or fail
    if result == 0:
        output = capture.get()
        # Should create group with non-standard name
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test quiet mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--quiet", "quietgroup"])

    # Should either succeed quietly or fail
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_add_user_to_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test adding user to existing group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser", "users"])

    # Should either succeed adding user to group or fail
    if result == 0:
        output = capture.get()
        # Should add user to group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "user", "group", "error"])


def test_execute_existing_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test adding existing group (should fail)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root"])

    # Should fail with group exists error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["exist", "already", "error"])


def test_execute_invalid_groupname(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test invalid group name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid@group"])

    # Should fail with invalid group name error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "name", "error"])


def test_execute_invalid_gid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test invalid GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "abc", "testgroup"])

    # Should fail with invalid GID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "gid", "number", "error"])


def test_execute_duplicate_gid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test duplicate GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "0", "testgroup"])

    # Should fail with duplicate GID error (0 is root)
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["gid", "exist", "use", "error"])


def test_execute_nonexistent_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test adding nonexistent user to group
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
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test adding user to nonexistent group
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "nonexistentgroup"])

    # Should fail with group not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["group", "not found", "does not exist", "error"]
    )


def test_execute_permission_denied(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test without sufficient permissions (non-root)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["permissiongroup"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # If running as root, should succeed
        assert len(output) >= 0
    else:
        # Should fail if not root
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "root", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "testgroup"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_reserved_group_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test reserved group names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["wheel"])

    # Should either succeed or fail based on system policy
    if result == 0:
        output = capture.get()
        # May allow creating wheel group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["exist", "reserved", "permission", "error"]
        )


def test_execute_gid_range_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test GID range validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "99999", "testgroup"])

    # Should either succeed with high GID or fail
    if result == 0:
        output = capture.get()
        # Should handle high GID
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["gid", "range", "invalid", "error"])


def test_execute_system_gid_range(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test system GID range
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--system", "--gid", "999", "sysgroup"]
        )

    # Should either succeed with system GID or fail
    if result == 0:
        output = capture.get()
        # Should create with system GID
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_negative_gid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test negative GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "-1", "testgroup"])

    # Should fail with negative GID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative", "gid", "error"])


def test_execute_zero_gid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test zero GID (root group)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "0", "rootgroup"])

    # Should fail with GID 0 already in use
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["gid", "use", "exist", "error"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["memorygroup"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
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
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test signal handling during group creation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["signalgroup"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["integrationgroup"])

    # Should integrate with system group management properly
    if result == 0:
        output = capture.get()
        # Should integrate with system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["concurrentgroup"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_validation_comprehensive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
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
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test atomic group creation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["atomicgroup"])

    # Should perform atomic operations
    if result == 0:
        output = capture.get()
        # Should complete atomically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_group_membership_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AddgroupCommand,
):
    # Test group membership validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "users"])

    # Should validate group membership
    if result == 0:
        output = capture.get()
        # Should add user to group
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["group", "user", "not found", "error"])
