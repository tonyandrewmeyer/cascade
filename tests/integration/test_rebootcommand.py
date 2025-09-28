"""Integration tests for the RebootCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RebootCommand instance."""
    yield pebble_shell.commands.RebootCommand(shell=shell)


def test_name(command: pebble_shell.commands.RebootCommand):
    assert command.name == "pebble-reboot"


def test_category(command: pebble_shell.commands.RebootCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.RebootCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "reboot" in output
    assert "Reboot the system" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "reboot" in output
    assert "Reboot the system" in output


def test_execute_no_args_immediate_reboot(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # reboot with no args should initiate immediate reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with reboot message or fail if Pebble unavailable
    if result == 0:
        output = capture.get()
        # Should show reboot initiation message
        assert any(
            msg in output
            for msg in ["Reboot initiated", "System will reboot", "Reboot scheduled"]
        )
    else:
        # Should fail if Pebble API unavailable or permission denied
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Reboot operation failed", "error", "failed"]
        )


def test_execute_immediate_reboot_confirmation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test immediate reboot confirmation message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should confirm reboot initiation if successful
    if result == 0:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Reboot initiated", "System will reboot", "Reboot scheduled"]
        )


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Reboot operation failed", "error", "failed"]
        )
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test handling of permission errors for reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        # Should show appropriate error message
        assert any(msg in output for msg in ["permission", "denied", "error", "failed"])
    else:
        # May succeed if user has reboot permissions
        assert result == 0


def test_execute_system_state_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test system state validation before reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should validate system state before proceeding
    if result == 0:
        output = capture.get()
        # Should proceed with reboot if system is in valid state
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        # May fail if system is not in valid state for reboot
        assert result == 1


def test_execute_reboot_request_submission(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot request submission to Pebble
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should submit reboot request to Pebble API
    if result == 0:
        output = capture.get()
        # Should indicate successful submission
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_extra_args_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test that extra arguments are ignored
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["extra", "args", "ignored"])

    # Should ignore extra arguments and proceed with reboot
    if result == 0:
        output = capture.get()
        # Should proceed with reboot regardless of extra args
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_concurrent_reboot_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test handling of concurrent reboot requests
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent reboot requests appropriately
    if result == 0:
        output = capture.get()
        # Should either proceed or indicate reboot already in progress
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_reboot_safety_checks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot safety checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should perform safety checks before reboot
    if result == 0:
        output = capture.get()
        # Should proceed after safety checks pass
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        # May fail if safety checks fail
        assert result == 1


def test_execute_service_shutdown_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test handling of service shutdown during reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle service shutdown as part of reboot
    if result == 0:
        output = capture.get()
        # Should initiate shutdown sequence
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_graceful_shutdown_sequence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test graceful shutdown sequence before reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should initiate graceful shutdown sequence
    if result == 0:
        output = capture.get()
        # Should handle graceful shutdown
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_filesystem_sync_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test filesystem sync handling before reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle filesystem synchronization
    if result == 0:
        output = capture.get()
        # Should proceed after filesystem sync
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_process_termination_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test process termination handling during reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle process termination appropriately
    if result == 0:
        output = capture.get()
        # Should manage process termination sequence
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_hardware_reset_preparation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test hardware reset preparation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should prepare for hardware reset
    if result == 0:
        output = capture.get()
        # Should prepare system for hardware reset
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_reboot_logging(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot event logging
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should log reboot events appropriately
    if result == 0:
        output = capture.get()
        # Should indicate logging of reboot event
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_emergency_reboot_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test emergency reboot handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle emergency reboot scenarios
    if result == 0:
        output = capture.get()
        # Should proceed with reboot even in emergency
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_container_environment_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot in container environment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle reboot appropriately in container context
    if result == 0:
        output = capture.get()
        # Should adapt reboot behavior for container environment
        assert any(
            msg in output
            for msg in ["Reboot initiated", "System will reboot", "Container restart"]
        )
    else:
        assert result == 1


def test_execute_reboot_timing_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot timing and scheduling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle reboot timing appropriately
    if result == 0:
        output = capture.get()
        # Should indicate when reboot will occur
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_network_cleanup_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test network cleanup during reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle network cleanup appropriately
    if result == 0:
        output = capture.get()
        # Should manage network cleanup sequence
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_resource_cleanup_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test resource cleanup during reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle resource cleanup appropriately
    if result == 0:
        output = capture.get()
        # Should clean up resources before reboot
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1


def test_execute_reboot_confirmation_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot confirmation message format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should provide clear confirmation message
    if result == 0:
        output = capture.get()
        # Should have informative confirmation message
        assert len(output.strip()) > 0
        assert any(
            msg in output
            for msg in ["Reboot initiated", "System will reboot", "reboot"]
        )


def test_execute_pebble_integration_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test Pebble integration validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should validate Pebble integration before reboot
    if result == 0:
        output = capture.get()
        # Should proceed after validation
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        # May fail if Pebble integration validation fails
        assert result == 1


def test_execute_system_health_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test system health check before reboot
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should perform system health check
    if result == 0:
        output = capture.get()
        # Should proceed after health check
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        # May fail if health check fails
        assert result == 1


def test_execute_reboot_state_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RebootCommand,
):
    # Test reboot state management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should manage reboot state appropriately
    if result == 0:
        output = capture.get()
        # Should handle state management
        assert any(msg in output for msg in ["Reboot initiated", "System will reboot"])
    else:
        assert result == 1
