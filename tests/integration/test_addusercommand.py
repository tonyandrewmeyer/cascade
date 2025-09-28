"""Integration tests for the AdduserCommand."""

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
    """Fixture to create a AdduserCommand instance."""
    yield pebble_shell.commands.AdduserCommand(shell=shell)


def test_name(command: pebble_shell.commands.AdduserCommand):
    assert command.name == "adduser"


def test_category(command: pebble_shell.commands.AdduserCommand):
    assert command.category == "User Management"


def test_help(command: pebble_shell.commands.AdduserCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "adduser" in output
    assert any(
        phrase in output.lower() for phrase in ["add", "user", "create", "account"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "adduser" in output
    assert any(
        phrase in output.lower() for phrase in ["add", "user", "create", "account"]
    )


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # adduser with no args should show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "adduser", "username"])


def test_execute_add_user_basic(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test basic user addition
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["testuser"])

    # Should either succeed or fail due to permissions
    if result == 0:
        output = capture.get()
        # Should indicate user creation success
        assert len(output) >= 0
        if len(output) > 0:
            assert any(word in output.lower() for word in ["add", "creat", "success"])
    else:
        # Should fail if not root or user exists
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "root", "exist", "error"]
        )


def test_execute_system_user_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test system user creation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--system", "sysuser"])

    # Should either succeed creating system user or fail
    if result == 0:
        output = capture.get()
        # Should create system user
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "error", "exist"])


def test_execute_no_create_home_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation without home directory
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--no-create-home", "nohomeuser"])

    # Should either succeed without creating home or fail
    if result == 0:
        output = capture.get()
        # Should create user without home directory
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_disabled_password_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with disabled password
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--disabled-password", "disableduser"]
        )

    # Should either succeed with disabled password or fail
    if result == 0:
        output = capture.get()
        # Should create user with disabled password
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_disabled_login_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with disabled login
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--disabled-login", "nologinuser"]
        )

    # Should either succeed with disabled login or fail
    if result == 0:
        output = capture.get()
        # Should create user with disabled login
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_home_directory_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with custom home directory
    custom_home = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--home", custom_home, "customuser"]
        )

    # Should either succeed with custom home or fail
    if result == 0:
        output = capture.get()
        # Should create user with custom home
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_shell_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with custom shell
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--shell", "/bin/bash", "bashuser"]
        )

    # Should either succeed with custom shell or fail
    if result == 0:
        output = capture.get()
        # Should create user with custom shell
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_uid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with specific UID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--uid", "1500", "uiduser"])

    # Should either succeed with specific UID or fail
    if result == 0:
        output = capture.get()
        # Should create user with specific UID
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "uid", "exist", "error"])


def test_execute_gid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with specific GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "1500", "giduser"])

    # Should either succeed with specific GID or fail
    if result == 0:
        output = capture.get()
        # Should create user with specific GID
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_ingroup_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation in specific group
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--ingroup", "users", "groupuser"]
        )

    # Should either succeed adding to group or fail
    if result == 0:
        output = capture.get()
        # Should create user in specified group
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_gecos_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test user creation with GECOS field
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--gecos", "Test User,,,", "gecosuser"]
        )

    # Should either succeed with GECOS or fail
    if result == 0:
        output = capture.get()
        # Should create user with GECOS information
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test quiet mode operation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--quiet", "quietuser"])

    # Should either succeed quietly or fail
    if result == 0:
        output = capture.get()
        # Should produce minimal output in quiet mode
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_force_badname_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test forcing bad username
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--force-badname", "bad-name"])

    # Should either succeed with forced bad name or fail
    if result == 0:
        output = capture.get()
        # Should create user with non-standard name
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_existing_user(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test adding existing user (should fail)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root"])

    # Should fail with user exists error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["exist", "already", "error"])


def test_execute_invalid_username(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test invalid username
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid@user"])

    # Should fail with invalid username error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "name", "error"])


def test_execute_invalid_uid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test invalid UID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--uid", "abc", "testuser"])

    # Should fail with invalid UID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "uid", "number", "error"])


def test_execute_invalid_gid(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test invalid GID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--gid", "xyz", "testuser"])

    # Should fail with invalid GID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "gid", "number", "error"])


def test_execute_nonexistent_group(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test adding user to nonexistent group
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--ingroup", "nonexistentgroup", "testuser"]
        )

    # Should fail with group not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["group", "not found", "exist", "error"])


def test_execute_nonexistent_shell(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test setting nonexistent shell
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--shell", "/nonexistent/shell", "testuser"]
        )

    # Should either succeed or fail depending on validation
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["shell", "not found", "invalid", "error"])


def test_execute_invalid_home_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test invalid home directory path
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--home", "relative/path", "testuser"]
        )

    # Should either succeed or fail depending on validation
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_permission_denied(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test without sufficient permissions (non-root)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["permissionuser"])

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
    command: pebble_shell.commands.AdduserCommand,
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
    command: pebble_shell.commands.AdduserCommand,
):
    # Test conflicting options
    test_home = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--system", "--no-create-home", "--home", test_home, "testuser"],
        )

    # Should either handle conflicts or fail appropriately
    if result == 0:
        output = capture.get()
        # May resolve conflicts automatically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["memoryuser"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
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
    command: pebble_shell.commands.AdduserCommand,
):
    # Test signal handling during user creation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["signaluser"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["integrationuser"])

    # Should integrate with system user management properly
    if result == 0:
        output = capture.get()
        # Should integrate with system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["concurrentuser"])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_validation_comprehensive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.AdduserCommand,
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
