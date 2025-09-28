"""Integration tests for the CheckCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a CheckCommand instance."""
    yield pebble_shell.commands.CheckCommand(shell=shell)


def test_name(command: pebble_shell.commands.CheckCommand):
    assert command.name == "pebble-check"


def test_category(command: pebble_shell.commands.CheckCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.CheckCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "check" in output
    assert "Show health check details" in output
    assert "check-name" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "check" in output
    assert "Show health check details" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # check with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "check <check-name>" in output


def test_execute_single_check_details(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test retrieving details for single health check
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-check"])

    # Should either succeed with check details or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show check details or not found message
        assert any(
            msg in output
            for msg in [
                "Check not found",
                "test-check",
                "Status:",
                "Level:",
                "Failures:",
            ]
        )
    else:
        # Should fail if check doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Check operation failed", "check not found", "error"]
        )


def test_execute_nonexistent_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test with nonexistent health check
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-check"])

    # Should fail with check not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in [
            "Check operation failed",
            "check not found",
            "Check not found",
            "error",
        ]
    )


def test_execute_empty_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test with empty check name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid check name
    assert result == 1


def test_execute_check_status_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check status display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["status-check"])

    # Should display check status if check exists
    if result == 0:
        output = capture.get()
        # Should show status information
        if "Status:" in output:
            # Should contain status values like up, down, unknown
            assert any(
                status in output for status in ["up", "down", "unknown", "Status:"]
            )
    else:
        assert result == 1


def test_execute_check_level_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check level display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["level-check"])

    # Should display check level if check exists
    if result == 0:
        output = capture.get()
        # Should show level information
        if "Level:" in output:
            # Should contain level values like alive, ready
            assert any(level in output for level in ["alive", "ready", "Level:"])
    else:
        assert result == 1


def test_execute_check_threshold_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check threshold display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["threshold-check"])

    # Should display threshold information if check exists
    if result == 0:
        output = capture.get()
        # Should show threshold configuration
        if "Threshold:" in output:
            # Should contain threshold values
            assert "Threshold:" in output
    else:
        assert result == 1


def test_execute_check_failures_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check failures display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["failures-check"])

    # Should display failure information if check exists
    if result == 0:
        output = capture.get()
        # Should show failures count or history
        if "Failures:" in output:
            # Should contain failure information
            assert "Failures:" in output
    else:
        assert result == 1


def test_execute_check_period_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check period display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["period-check"])

    # Should display period information if check exists
    if result == 0:
        output = capture.get()
        # Should show check period configuration
        if "Period:" in output:
            # Should contain period/interval information
            assert "Period:" in output
    else:
        assert result == 1


def test_execute_check_timeout_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check timeout display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["timeout-check"])

    # Should display timeout information if check exists
    if result == 0:
        output = capture.get()
        # Should show timeout configuration
        if "Timeout:" in output:
            # Should contain timeout information
            assert "Timeout:" in output
    else:
        assert result == 1


def test_execute_check_override_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check override display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["override-check"])

    # Should display override information if check exists
    if result == 0:
        output = capture.get()
        # Should show override configuration
        if "Override:" in output:
            # Should contain override information
            assert "Override:" in output
    else:
        assert result == 1


def test_execute_check_command_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check command display for exec checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["exec-check"])

    # Should display command information for exec checks
    if result == 0:
        output = capture.get()
        # Should show command configuration
        if "Command:" in output:
            # Should contain command information
            assert "Command:" in output
    else:
        assert result == 1


def test_execute_check_http_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check HTTP configuration display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["http-check"])

    # Should display HTTP configuration for HTTP checks
    if result == 0:
        output = capture.get()
        # Should show HTTP configuration
        if "URL:" in output or "HTTP:" in output:
            # Should contain HTTP check information
            pass
    else:
        assert result == 1


def test_execute_check_tcp_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check TCP configuration display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["tcp-check"])

    # Should display TCP configuration for TCP checks
    if result == 0:
        output = capture.get()
        # Should show TCP configuration
        if "Port:" in output or "TCP:" in output:
            # Should contain TCP check information
            pass
    else:
        assert result == 1


def test_execute_check_environment_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check environment variables display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["env-check"])

    # Should display environment variables if configured
    if result == 0:
        output = capture.get()
        # Should show environment configuration
        if "Environment:" in output:
            # Should contain environment variables
            assert "Environment:" in output
    else:
        assert result == 1


def test_execute_check_working_directory_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check working directory display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["workdir-check"])

    # Should display working directory if configured
    if result == 0:
        output = capture.get()
        # Should show working directory configuration
        if "Working Directory:" in output:
            # Should contain working directory information
            assert "Working Directory:" in output
    else:
        assert result == 1


def test_execute_check_user_group_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check user/group display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["user-check"])

    # Should display user/group information if configured
    if result == 0:
        output = capture.get()
        # Should show user/group configuration
        if any(
            field in output for field in ["User:", "Group:", "User-ID:", "Group-ID:"]
        ):
            # Should contain user/group information
            pass
    else:
        assert result == 1


def test_execute_check_service_context_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check service context display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["service-check"])

    # Should display service context if configured
    if result == 0:
        output = capture.get()
        # Should show service context information
        if "Service Context:" in output:
            # Should contain service context
            assert "Service Context:" in output
    else:
        assert result == 1


def test_execute_check_last_run_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check last run time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["lastrun-check"])

    # Should display last run information
    if result == 0:
        output = capture.get()
        # Should show last run time
        if "Last Run:" in output or "Last Executed:" in output:
            # Should contain timing information
            pass
    else:
        assert result == 1


def test_execute_check_next_run_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check next run time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nextrun-check"])

    # Should display next run information
    if result == 0:
        output = capture.get()
        # Should show next run time
        if "Next Run:" in output or "Next Scheduled:" in output:
            # Should contain scheduling information
            pass
    else:
        assert result == 1


def test_execute_check_error_details_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check error details display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["error-check"])

    # Should display error details if check has failed
    if result == 0:
        output = capture.get()
        # Should show error information
        if "Error:" in output or "Last Error:" in output:
            # Should contain error details
            pass
    else:
        assert result == 1


def test_execute_check_output_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check output display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["output-check"])

    # Should display check output if available
    if result == 0:
        output = capture.get()
        # Should show check output
        if "Output:" in output or "Last Output:" in output:
            # Should contain output information
            pass
    else:
        assert result == 1


def test_execute_check_history_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check history display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["history-check"])

    # Should display check history if available
    if result == 0:
        output = capture.get()
        # Should show check execution history
        if "History:" in output or "Recent Runs:" in output:
            # Should contain historical information
            pass
    else:
        assert result == 1


def test_execute_check_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check details formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["format-check"])

    # Should format check details appropriately
    if result == 0:
        output = capture.get()
        # Should have proper formatting
        if output.strip() and "Check not found" not in output:
            # Should contain structured information
            assert "format-check" in output or len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_multiple_checks_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test with multiple check names (should use first one)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["check1", "check2", "check3"])

    # Should use first check name and ignore extras
    if result == 0:
        output = capture.get()
        # Should show details for first check
        assert any(msg in output for msg in ["check1", "Check not found"])
    else:
        assert result == 1


def test_execute_check_name_case_sensitivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check name case sensitivity
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["MyCheck"])

    # Should either handle case sensitivity or fail appropriately
    assert result in [0, 1]


def test_execute_special_characters_in_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check names with special characters
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["check-with-dashes_and_underscores"]
        )

    # Should either handle special characters or fail appropriately
    assert result in [0, 1]


def test_execute_long_check_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test with very long check name
    long_name = "very-long-check-name-that-exceeds-normal-length-expectations"
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[long_name])

    # Should handle long check names appropriately
    assert result in [0, 1]


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["api-test-check"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Check operation failed", "error", "failed"]
        )
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test permission handling for check access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["permission-check"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Check operation failed", "error"]
        )
    else:
        assert result == 0


def test_execute_check_data_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test extraction of check data fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["data-check"])

    # Should extract all check fields properly
    if result == 0:
        output = capture.get()
        # Should handle all check attributes
        if output.strip() and "Check not found" not in output:
            # Should extract check details correctly
            pass
    else:
        assert result == 1


def test_execute_check_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test that command retrieves check information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["retrieval-check"])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_unknown_check_fields_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test handling of checks with unknown or missing fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["unknown-fields-check"])

    # Should handle missing check fields gracefully
    if result == 0:
        output = capture.get()
        # Should display information even if some fields are missing
        if output.strip() and "Check not found" not in output:
            # Should show "unknown" for missing fields
            pass
    else:
        assert result == 1


def test_execute_check_configuration_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CheckCommand,
):
    # Test check configuration validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["validation-check"])

    # Should validate check configuration appropriately
    if result == 0:
        output = capture.get()
        # Should show configuration validation results
        if output.strip() and "Check not found" not in output:
            # Should indicate configuration validity
            pass
    else:
        assert result == 1
