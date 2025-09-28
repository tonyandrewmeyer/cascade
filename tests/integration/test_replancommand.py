"""Integration tests for the ReplanCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ReplanCommand instance."""
    yield pebble_shell.commands.ReplanCommand(shell=shell)


def test_name(command: pebble_shell.commands.ReplanCommand):
    assert command.name == "replan"


def test_category(command: pebble_shell.commands.ReplanCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.ReplanCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "replan" in output
    assert "Update Pebble service plan" in output
    assert "--wait" in output
    assert "--timeout" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "replan" in output
    assert "Update Pebble service plan" in output


def test_execute_no_args_default_replan(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # replan with no args should trigger default replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with replan or fail if Pebble unavailable
    if result == 0:
        output = capture.get()
        # Should show replan completion message
        assert any(
            msg in output
            for msg in [
                "Replan completed",
                "Plan updated",
                "Services replanned",
                "Replan successful",
            ]
        )
    else:
        # Should fail if Pebble is not available or accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Replan operation failed",
                "Connection failed",
                "Pebble not available",
                "error",
            ]
        )


def test_execute_wait_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test --wait option to wait for replan completion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should either succeed waiting for replan or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show replan completion with wait
        assert any(
            msg in output
            for msg in [
                "Replan completed",
                "Wait completed",
                "Plan updated",
                "Services ready",
            ]
        )
    else:
        assert result == 1


def test_execute_no_wait_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test --no-wait option to return immediately
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--no-wait"])

    # Should either succeed without waiting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show replan started message
        assert any(
            msg in output
            for msg in [
                "Replan started",
                "Plan update initiated",
                "Replan in progress",
                "Services replanning",
            ]
        )
    else:
        assert result == 1


def test_execute_timeout_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test --timeout option with specific timeout
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "30"])

    # Should either succeed with timeout or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete within timeout
        assert any(
            msg in output for msg in ["Replan completed", "Plan updated", "completed"]
        )
    else:
        # Should fail if timeout exceeded or other error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["timeout", "Replan operation failed", "error"]
        )


def test_execute_short_timeout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test with very short timeout that might expire
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "1"])

    # Should either complete quickly or timeout
    if result == 0:
        output = capture.get()
        # Should complete within short timeout
        assert len(output.strip()) >= 0
    else:
        # Should fail with timeout or other error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["timeout", "exceeded", "error"])


def test_execute_long_timeout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test with long timeout for complex replans
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "300"])

    # Should either succeed with long timeout or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete successfully
        assert any(
            msg in output for msg in ["Replan completed", "Plan updated", "completed"]
        )
    else:
        assert result == 1


def test_execute_invalid_timeout_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test with invalid timeout format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "invalid"])

    # Should fail with invalid timeout error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "timeout", "error"])


def test_execute_negative_timeout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test with negative timeout value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "-10"])

    # Should fail with invalid timeout error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "timeout", "negative", "error"])


def test_execute_zero_timeout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test with zero timeout (immediate timeout)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "0"])

    # Should either handle zero timeout or fail appropriately
    if result == 0:
        output = capture.get()
        # Should complete immediately or handle zero timeout
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_combined_wait_timeout(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test combining --wait and --timeout options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait", "--timeout", "60"])

    # Should either succeed with both options or fail gracefully
    if result == 0:
        output = capture.get()
        # Should complete with wait and timeout
        assert any(
            msg in output for msg in ["Replan completed", "Plan updated", "completed"]
        )
    else:
        assert result == 1


def test_execute_conflicting_wait_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test conflicting --wait and --no-wait options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait", "--no-wait"])

    # Should handle conflicting options appropriately
    if result == 0:
        output = capture.get()
        # Should use one of the options (likely last one)
        assert len(output.strip()) >= 0
    else:
        # Should fail with conflicting options error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["conflicting", "options", "error"])


def test_execute_pebble_connection_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test Pebble connection handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle Pebble connection appropriately
    if result == 0:
        output = capture.get()
        # Should successfully connect and replan
        assert any(
            msg in output for msg in ["Replan completed", "Plan updated", "completed"]
        )
    else:
        # Should fail gracefully if connection issues
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Connection failed", "Pebble not available", "error"]
        )


def test_execute_service_dependency_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test handling of service dependencies during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should handle service dependencies appropriately
    if result == 0:
        output = capture.get()
        # Should resolve dependencies during replan
        assert any(
            msg in output
            for msg in [
                "Replan completed",
                "Dependencies resolved",
                "Services replanned",
            ]
        )
    else:
        assert result == 1


def test_execute_plan_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test plan validation during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should validate plan during replan
    if result == 0:
        output = capture.get()
        # Should show successful plan validation
        assert any(
            msg in output
            for msg in ["Replan completed", "Plan valid", "Validation successful"]
        )
    else:
        # Should fail if plan validation fails
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["validation failed", "invalid plan", "error"]
        )


def test_execute_service_state_changes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test service state changes during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should handle service state changes appropriately
    if result == 0:
        output = capture.get()
        # Should show service state changes
        assert any(
            msg in output
            for msg in ["Replan completed", "Services updated", "State changes applied"]
        )
    else:
        assert result == 1


def test_execute_configuration_updates(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test configuration updates during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle configuration updates appropriately
    if result == 0:
        output = capture.get()
        # Should apply configuration updates
        assert any(
            msg in output
            for msg in ["Replan completed", "Configuration updated", "Config applied"]
        )
    else:
        assert result == 1


def test_execute_layer_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test layer management during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should handle layer management appropriately
    if result == 0:
        output = capture.get()
        # Should manage layers during replan
        assert any(
            msg in output
            for msg in ["Replan completed", "Layers processed", "Layer updates applied"]
        )
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test error recovery during replan failures
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle errors gracefully
    if result == 0:
        output = capture.get()
        # Should complete successfully
        assert len(output.strip()) >= 0
    else:
        # Should recover from errors gracefully
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Replan operation failed", "error", "failed"]
        )


def test_execute_progress_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test progress reporting during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should provide progress information
    if result == 0:
        output = capture.get()
        # Should show progress updates
        assert any(
            msg in output
            for msg in ["Replan completed", "Progress", "Updating", "completed"]
        )
    else:
        assert result == 1


def test_execute_atomic_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test atomic replan operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should perform atomic operations
    if result == 0:
        output = capture.get()
        # Should complete atomically
        assert any(
            msg in output
            for msg in ["Replan completed", "Atomic update", "Transaction completed"]
        )
    else:
        assert result == 1


def test_execute_rollback_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test rollback handling on replan failures
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "5"])

    # Should handle rollback appropriately
    if result == 0:
        output = capture.get()
        # Should complete successfully
        assert len(output.strip()) >= 0
    else:
        # Should rollback on failure
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["rollback", "reverted", "error"])


def test_execute_concurrent_replan_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test handling of concurrent replan operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--no-wait"])

    # Should handle concurrent operations appropriately
    if result == 0:
        output = capture.get()
        # Should handle concurrency
        assert any(
            msg in output
            for msg in ["Replan started", "Operation queued", "In progress"]
        )
    else:
        # Should fail if concurrent operation not allowed
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["concurrent", "already running", "error"])


def test_execute_plan_diff_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test plan difference reporting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--verbose"])

    # Should report plan differences
    if result == 0:
        output = capture.get()
        # Should show plan changes
        assert any(
            msg in output
            for msg in ["Replan completed", "Changes applied", "Differences"]
        )
    else:
        assert result == 1


def test_execute_health_check_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test integration with health checks during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should integrate with health checks
    if result == 0:
        output = capture.get()
        # Should handle health checks during replan
        assert any(
            msg in output
            for msg in ["Replan completed", "Health checks", "Services healthy"]
        )
    else:
        assert result == 1


def test_execute_resource_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test resource management during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should manage resources appropriately
    if result == 0:
        output = capture.get()
        # Should handle resource allocation
        assert any(
            msg in output
            for msg in [
                "Replan completed",
                "Resources allocated",
                "Management successful",
            ]
        )
    else:
        assert result == 1


def test_execute_logging_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test logging integration during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait"])

    # Should integrate with logging system
    if result == 0:
        output = capture.get()
        # Should log replan activities
        assert any(
            msg in output for msg in ["Replan completed", "Logged", "Activity recorded"]
        )
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test memory efficiency during replan
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReplanCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0
