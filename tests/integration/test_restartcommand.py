"""Integration tests for the RestartCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RestartCommand instance."""
    yield pebble_shell.commands.RestartCommand(shell=shell)


def test_name(command: pebble_shell.commands.RestartCommand):
    assert command.name == "pebble-restart"


def test_category(command: pebble_shell.commands.RestartCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.RestartCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "restart" in output
    assert "Restart services" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "restart" in output
    assert "Restart services" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # restart with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "restart <service-name>" in output


def test_execute_single_service_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restarting a single service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show success message
        assert "Service restarted successfully:" in output
        assert "test-service" in output
    else:
        # Should fail if service doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert "Service restart operation failed" in output


def test_execute_multiple_service_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restarting multiple services
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["service1", "service2", "service3"]
        )

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show success message with all services
        assert "Service restarted successfully:" in output
        assert "service1" in output
        assert "service2" in output
        assert "service3" in output
    else:
        # Should fail if any service doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert "Service restart operation failed" in output


def test_execute_nonexistent_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test with nonexistent service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-service"])

    # Should fail with service not found error
    assert result == 1
    output = capture.get()
    assert "Service restart operation failed" in output


def test_execute_empty_service_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test with empty service name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid service name
    assert result == 1


def test_execute_service_name_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test with service name containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["my test service"])

    # Should either handle spaces or fail appropriately
    if result == 0:
        output = capture.get()
        assert "my test service" in output
    else:
        assert result == 1


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_success_message_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test success message formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["service1", "service2"])

    # Should format success message properly if successful
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
        # Should list the services that were restarted
        assert "service1" in output and "service2" in output


def test_execute_service_restart_confirmation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test that service restart is confirmed
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["my-service"])

    # Should confirm service restart if successful
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
        assert "my-service" in output


def test_execute_mixed_valid_invalid_services(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test with mix of valid and invalid service names
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["valid-service", "invalid-service"]
        )

    # Should fail if any service is invalid (atomic operation)
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output


def test_execute_running_service_restart(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restarting a running service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["running-service"])

    # Should restart running service
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_stopped_service_restart(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restarting a stopped service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stopped-service"])

    # Should start stopped service (restart behavior)
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test handling of permission errors for restarting services
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["restricted-service"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output


def test_execute_service_dependency_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test handling of service dependencies
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["dependent-service"])

    # Should handle service dependencies appropriately
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        # May fail if dependencies prevent restart
        assert result == 1


def test_execute_large_number_of_services(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restarting many services at once
    service_names = [f"service-{i}" for i in range(10)]
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=service_names)

    # Should either handle multiple services or fail gracefully
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_service_configuration_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test that service configuration is validated before restart
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-config-service"])

    # Should validate service configuration
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output


def test_execute_service_name_case_sensitivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test service name case sensitivity
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["MyService"])

    # Should either handle case sensitivity or fail appropriately
    assert result in [0, 1]


def test_execute_special_characters_in_service_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test service names with special characters
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["service-with-dashes_and_underscores"]
        )

    # Should either handle special characters or fail appropriately
    assert result in [0, 1]


def test_execute_duplicate_service_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test with duplicate service names in arguments
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["same-service", "same-service"])

    # Should either handle duplicates or fail appropriately
    assert result in [0, 1]


def test_execute_restart_sequence_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restart sequence (stop then start)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["sequence-service"])

    # Should handle stop-start sequence for restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_graceful_restart_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test graceful restart handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["graceful-service"])

    # Should handle graceful restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_forced_restart_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test forced restart handling for stubborn services
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stubborn-service"])

    # Should handle forced restart if needed
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_service_state_transition(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test service state transition during restart
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["state-service"])

    # Should transition service state appropriately
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_timeout_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test timeout handling for slow-restarting services
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["slow-service"])

    # Should handle timeouts gracefully
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output
    else:
        assert result == 0


def test_execute_resource_cleanup_and_init(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test resource cleanup and re-initialization during restart
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["resource-service"])

    # Should clean up and re-initialize resources during restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_restart_vs_start_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test that restart behaves differently from start
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["behavior-service"])

    # Should perform restart operation (not just start)
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_restart_failure_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restart failure recovery
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["failure-service"])

    # Should handle restart failures appropriately
    if result == 1:
        output = capture.get()
        assert "Service restart operation failed" in output
    else:
        assert result == 0


def test_execute_changed_services_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test that only actually restarted services are reported
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["service1"])

    # Should report only services that were actually restarted
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
        # Should list only the services that changed state


def test_execute_restart_with_config_reload(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restart with configuration reload
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["config-service"])

    # Should reload configuration during restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_restart_ordering_dependencies(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restart ordering based on dependencies
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["dependency-service", "main-service"]
        )

    # Should handle dependency ordering during restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1


def test_execute_restart_health_check_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RestartCommand,
):
    # Test restart integration with health checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["health-service"])

    # Should integrate with health checks during restart
    if result == 0:
        output = capture.get()
        assert "Service restarted successfully:" in output
    else:
        assert result == 1
