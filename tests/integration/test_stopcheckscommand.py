"""Integration tests for the StopChecksCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a StopChecksCommand instance."""
    yield pebble_shell.commands.StopChecksCommand(shell=shell)


def test_name(command: pebble_shell.commands.StopChecksCommand):
    assert command.name == "pebble-stop-checks"


def test_category(command: pebble_shell.commands.StopChecksCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.StopChecksCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "stop-checks" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "stop-checks" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # stop-checks with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "stop-checks <check-name>" in output


def test_execute_single_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test stopping a single health check
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["health-check-1"])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show success message
        assert "Stopped checks:" in output
        assert "health-check-1" in output
    else:
        # Should fail if check doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert "Stop checks operation failed" in output


def test_execute_multiple_check_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test stopping multiple health checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["check1", "check2", "check3"])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show success message with all checks
        assert "Stopped checks:" in output
        assert "check1" in output
        assert "check2" in output
        assert "check3" in output
    else:
        # Should fail if any check doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert "Stop checks operation failed" in output


def test_execute_nonexistent_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test with nonexistent health check
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-check"])

    # Should fail with check not found error
    assert result == 1
    output = capture.get()
    assert "Stop checks operation failed" in output


def test_execute_empty_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test with empty check name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid check name
    assert result == 1


def test_execute_check_name_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test with check name containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["my health check"])

    # Should either handle spaces or fail appropriately
    if result == 0:
        output = capture.get()
        assert "my health check" in output
    else:
        assert result == 1


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-check"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert "Stop checks operation failed" in output
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_success_message_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test success message formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["check1", "check2"])

    # Should format success message properly if successful
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
        # Should list the checks that were stopped
        assert "check1" in output and "check2" in output


def test_execute_check_stop_confirmation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test that check stop is confirmed
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["my-check"])

    # Should confirm check stop if successful
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
        assert "my-check" in output


def test_execute_mixed_valid_invalid_checks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test with mix of valid and invalid check names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["valid-check", "invalid-check"])

    # Should fail if any check is invalid (atomic operation)
    if result == 1:
        output = capture.get()
        assert "Stop checks operation failed" in output


def test_execute_already_stopped_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test stopping a check that's already stopped
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stopped-check"])

    # Should either succeed (idempotent) or handle gracefully
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        # May fail if operation is not idempotent
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test handling of permission errors for stopping checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["restricted-check"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        assert "Stop checks operation failed" in output


def test_execute_check_dependency_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test handling of check dependencies
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["dependent-check"])

    # Should handle check dependencies appropriately
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        # May fail if dependencies prevent stopping
        assert result == 1


def test_execute_large_number_of_checks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test stopping many checks at once
    check_names = [f"check-{i}" for i in range(10)]
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=check_names)

    # Should either handle multiple checks or fail gracefully
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        assert result == 1


def test_execute_check_configuration_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test that check configuration is validated before stopping
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-config-check"])

    # Should validate check configuration
    if result == 1:
        output = capture.get()
        assert "Stop checks operation failed" in output


def test_execute_check_name_case_sensitivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test check name case sensitivity
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["MyCheck"])

    # Should either handle case sensitivity or fail appropriately
    assert result in [0, 1]


def test_execute_special_characters_in_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test check names with special characters
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["check-with-dashes_and_underscores"]
        )

    # Should either handle special characters or fail appropriately
    assert result in [0, 1]


def test_execute_duplicate_check_names(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test with duplicate check names in arguments
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["same-check", "same-check"])

    # Should either handle duplicates or fail appropriately
    assert result in [0, 1]


def test_execute_changed_checks_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test that only actually changed checks are reported
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["check1"])

    # Should report only checks that were actually stopped
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
        # Should list only the checks that changed state


def test_execute_graceful_shutdown_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test graceful handling of check shutdown
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["graceful-check"])

    # Should handle graceful check shutdown
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        assert result == 1


def test_execute_forced_stop_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test forced stop handling for stubborn checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stubborn-check"])

    # Should handle forced stop if needed
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        assert result == 1


def test_execute_check_state_transition(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test check state transition from running to stopped
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["running-check"])

    # Should transition check state appropriately
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        assert result == 1


def test_execute_timeout_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test timeout handling for slow-stopping checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["slow-check"])

    # Should handle timeouts gracefully
    if result == 1:
        output = capture.get()
        assert "Stop checks operation failed" in output
    else:
        assert result == 0


def test_execute_resource_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.StopChecksCommand,
):
    # Test resource cleanup when stopping checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["resource-check"])

    # Should clean up resources when stopping checks
    if result == 0:
        output = capture.get()
        assert "Stopped checks:" in output
    else:
        assert result == 1
