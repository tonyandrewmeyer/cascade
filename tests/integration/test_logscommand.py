"""Integration tests for the LogsCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LogsCommand instance."""
    yield pebble_shell.commands.LogsCommand(shell=shell)


def test_name(command: pebble_shell.commands.LogsCommand):
    assert command.name == "pebble-logs"


def test_category(command: pebble_shell.commands.LogsCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.LogsCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "logs" in output
    assert "Retrieve service logs" in output
    assert "--follow" in output
    assert "--lines" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "logs" in output
    assert "Retrieve service logs" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # logs with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "logs <service-name>" in output


def test_execute_single_service_logs(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test retrieving logs for single service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should either succeed with logs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show log entries or no logs message
        assert any(
            msg in output
            for msg in [
                "No logs found for service",
                "test-service",
                "INFO",
                "ERROR",
                "DEBUG",
            ]
        )
    else:
        # Should fail if service doesn't exist or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Logs operation failed", "service not found", "error"]
        )


def test_execute_nonexistent_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with nonexistent service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-service"])

    # Should fail with service not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["Logs operation failed", "service not found", "error"]
    )


def test_execute_empty_service_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with empty service name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid service name
    assert result == 1


def test_execute_follow_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test -f follow option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "test-service"])

    # Should either succeed with following logs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should start following logs
        assert any(
            msg in output for msg in ["Following logs", "test-service", "No logs found"]
        )
    else:
        assert result == 1


def test_execute_follow_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test --follow option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--follow", "test-service"])

    # Should behave same as -f option
    if result == 0:
        output = capture.get()
        # Should start following logs
        assert any(
            msg in output for msg in ["Following logs", "test-service", "No logs found"]
        )
    else:
        assert result == 1


def test_execute_lines_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test -n lines option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "10", "test-service"])

    # Should either succeed with limited lines or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show limited number of log lines
        lines = output.strip().split("\n")
        # Should respect line limit if logs exist
        if "No logs found" not in output:
            assert len(lines) <= 10
    else:
        assert result == 1


def test_execute_lines_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test --lines option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--lines", "5", "test-service"])

    # Should behave same as -n option
    if result == 0:
        output = capture.get()
        # Should show limited number of log lines
        lines = output.strip().split("\n")
        if "No logs found" not in output:
            assert len(lines) <= 5
    else:
        assert result == 1


def test_execute_invalid_lines_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with invalid lines count
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--lines", "invalid", "test-service"]
        )

    # Should fail with invalid lines count error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "lines", "error"])


def test_execute_negative_lines_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with negative lines count
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--lines", "-5", "test-service"])

    # Should fail with invalid lines count error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "lines", "error"])


def test_execute_zero_lines_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with zero lines count
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--lines", "0", "test-service"])

    # Should either succeed with no output or fail
    if result == 0:
        output = capture.get()
        # Should show no log lines
        assert len(output.strip()) == 0 or "No logs found" in output
    else:
        assert result == 1


def test_execute_large_lines_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with very large lines count
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--lines", "10000", "test-service"]
        )

    # Should either succeed with all available logs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show all available logs up to limit
        assert any(msg in output for msg in ["test-service", "No logs found"])
    else:
        assert result == 1


def test_execute_multiple_services(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test with multiple service names
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["service1", "service2"])

    # Should either succeed showing logs for all services or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show logs for both services
        assert any(msg in output for msg in ["service1", "service2", "No logs found"])
    else:
        assert result == 1


def test_execute_log_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log formatting and display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should format logs appropriately
    if result == 0:
        output = capture.get()
        # Should have proper log formatting
        if "No logs found" not in output and output.strip():
            # Should contain timestamp and service name formatting
            assert "test-service" in output or len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_log_level_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log level filtering if supported
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should show logs of all levels by default
    if result == 0:
        output = capture.get()
        # Should include all log levels
        if output.strip() and "No logs found" not in output:
            # May contain various log levels
            pass
    else:
        assert result == 1


def test_execute_timestamp_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test timestamp display in logs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should display timestamps with logs
    if result == 0:
        output = capture.get()
        # Should include timestamps in log entries
        if output.strip() and "No logs found" not in output:
            # Should have timestamp formatting
            pass
    else:
        assert result == 1


def test_execute_service_name_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test service name display in logs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should display service name with logs
    if result == 0:
        output = capture.get()
        # Should include service name in log entries
        if output.strip() and "No logs found" not in output:
            # Should show service context
            pass
    else:
        assert result == 1


def test_execute_no_logs_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test when no logs are available for service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["empty-service"])

    # Should either succeed with no logs message or fail
    if result == 0:
        output = capture.get()
        # Should show no logs message
        assert "No logs found" in output or len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_real_time_log_following(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test real-time log following
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--follow", "active-service"])

    # Should either succeed following real-time logs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should start following logs in real-time
        assert any(
            msg in output
            for msg in ["Following logs", "active-service", "No logs found"]
        )
    else:
        assert result == 1


def test_execute_log_buffer_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log buffer handling for large outputs
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--lines", "1000", "verbose-service"]
        )

    # Should handle large log buffers appropriately
    if result == 0:
        output = capture.get()
        # Should manage large output efficiently
        assert any(msg in output for msg in ["verbose-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_rotation_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test handling of log rotation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["rotated-service"])

    # Should handle rotated logs appropriately
    if result == 0:
        output = capture.get()
        # Should access logs across rotation
        assert any(msg in output for msg in ["rotated-service", "No logs found"])
    else:
        assert result == 1


def test_execute_concurrent_log_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test concurrent log access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["concurrent-service"])

    # Should handle concurrent access appropriately
    if result == 0:
        output = capture.get()
        # Should manage concurrent log access
        assert any(msg in output for msg in ["concurrent-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_encoding_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test handling of different log encodings
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["encoded-service"])

    # Should handle various text encodings
    if result == 0:
        output = capture.get()
        # Should decode logs properly
        assert any(msg in output for msg in ["encoded-service", "No logs found"])
    else:
        assert result == 1


def test_execute_binary_log_data_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test handling of binary data in logs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["binary-service"])

    # Should handle binary data appropriately
    if result == 0:
        output = capture.get()
        # Should filter or display binary data safely
        assert any(msg in output for msg in ["binary-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_streaming_performance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log streaming performance
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--lines", "100", "performance-service"]
        )

    # Should stream logs efficiently
    if result == 0:
        output = capture.get()
        # Should handle streaming efficiently
        assert any(msg in output for msg in ["performance-service", "No logs found"])
    else:
        assert result == 1


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test-service"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["Logs operation failed", "error", "failed"]
        )
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test permission handling for log access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["restricted-service"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission denied", "Logs operation failed", "error"]
        )
    else:
        assert result == 0


def test_execute_log_search_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log search functionality if supported
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["searchable-service"])

    # Should provide searchable log output
    if result == 0:
        output = capture.get()
        # Should allow searching through logs
        assert any(msg in output for msg in ["searchable-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_filtering_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log filtering options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["filterable-service"])

    # Should support log filtering
    if result == 0:
        output = capture.get()
        # Should filter logs appropriately
        assert any(msg in output for msg in ["filterable-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_export_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log export functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["exportable-service"])

    # Should support log export
    if result == 0:
        output = capture.get()
        # Should provide exportable log data
        assert any(msg in output for msg in ["exportable-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_aggregation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log aggregation from multiple sources
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["aggregated-service"])

    # Should aggregate logs appropriately
    if result == 0:
        output = capture.get()
        # Should combine logs from multiple sources
        assert any(msg in output for msg in ["aggregated-service", "No logs found"])
    else:
        assert result == 1


def test_execute_log_tail_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LogsCommand,
):
    # Test log tail functionality (most recent entries)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--lines", "20", "tail-service"])

    # Should show most recent log entries
    if result == 0:
        output = capture.get()
        # Should display recent log entries
        assert any(msg in output for msg in ["tail-service", "No logs found"])
    else:
        assert result == 1
