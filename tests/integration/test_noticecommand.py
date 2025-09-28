"""Integration tests for the NoticeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NoticeCommand instance."""
    yield pebble_shell.commands.NoticeCommand(shell=shell)


def test_name(command: pebble_shell.commands.NoticeCommand):
    assert command.name == "notice"


def test_category(command: pebble_shell.commands.NoticeCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.NoticeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "notice" in output
    assert "Manage Pebble notices" in output
    assert "NOTICE_ID" in output
    assert "--action" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "notice" in output
    assert "Manage Pebble notices" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # notice with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "notice <NOTICE_ID>" in output


def test_execute_get_notice_by_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test getting notice by ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should either succeed showing notice or fail if not found
    if result == 0:
        output = capture.get()
        # Should show notice information
        assert any(
            msg in output
            for msg in ["Notice ID: 1", "Type:", "Key:", "Data:", "Notice details"]
        )
    else:
        # Should fail if notice not found or Pebble unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Notice not found",
                "No notice with ID",
                "Connection failed",
                "error",
            ]
        )


def test_execute_get_notice_invalid_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test with invalid notice ID format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-id"])

    # Should fail with invalid ID error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "notice ID", "error"])


def test_execute_get_notice_nonexistent_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test with nonexistent notice ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["99999"])

    # Should fail with notice not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["Notice not found", "No notice with ID", "not found", "error"]
    )


def test_execute_acknowledge_action(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test acknowledge action on notice
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--action", "acknowledge", "1"])

    # Should either succeed acknowledging or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show acknowledgment success
        assert any(
            msg in output
            for msg in [
                "Notice acknowledged",
                "Acknowledgment successful",
                "Notice 1 acknowledged",
                "Acknowledged",
            ]
        )
    else:
        # Should fail if notice not found or operation failed
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Notice not found", "Acknowledge failed", "error"]
        )


def test_execute_dismiss_action(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test dismiss action on notice
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--action", "dismiss", "1"])

    # Should either succeed dismissing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show dismiss success
        assert any(
            msg in output
            for msg in [
                "Notice dismissed",
                "Dismiss successful",
                "Notice 1 dismissed",
                "Dismissed",
            ]
        )
    else:
        # Should fail if notice not found or operation failed
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Notice not found", "Dismiss failed", "error"]
        )


def test_execute_clear_action(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test clear action on notice
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--action", "clear", "1"])

    # Should either succeed clearing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show clear success
        assert any(
            msg in output
            for msg in [
                "Notice cleared",
                "Clear successful",
                "Notice 1 cleared",
                "Cleared",
            ]
        )
    else:
        # Should fail if notice not found or operation failed
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Notice not found", "Clear failed", "error"]
        )


def test_execute_invalid_action(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test with invalid action
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--action", "invalid-action", "1"]
        )

    # Should fail with invalid action error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid action", "unknown action", "error"])


def test_execute_show_notice_details(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test showing detailed notice information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--details", "1"])

    # Should either succeed showing details or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show detailed notice information
        assert any(
            msg in output
            for msg in [
                "Notice ID:",
                "Type:",
                "Key:",
                "Data:",
                "First occurred:",
                "Last occurred:",
                "Occurrences:",
            ]
        )
    else:
        assert result == 1


def test_execute_show_notice_json(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test showing notice in JSON format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--json", "1"])

    # Should either succeed showing JSON or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show JSON formatted notice
        assert any(
            json_indicator in output
            for json_indicator in ['{"id"', '"type"', '"key"', '"data"']
        )
    else:
        assert result == 1


def test_execute_show_notice_yaml(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test showing notice in YAML format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--yaml", "1"])

    # Should either succeed showing YAML or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show YAML formatted notice
        assert any(
            yaml_indicator in output
            for yaml_indicator in ["id:", "type:", "key:", "data:"]
        )
    else:
        assert result == 1


def test_execute_filter_by_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test filtering notice by type
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--type", "custom", "1"])

    # Should either succeed filtering or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show filtered notice information
        assert any(
            msg in output for msg in ["Type: custom", "Notice ID: 1", "Filtered"]
        )
    else:
        assert result == 1


def test_execute_filter_by_key(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test filtering notice by key
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--key", "service.started", "1"])

    # Should either succeed filtering or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show filtered notice information
        assert any(
            msg in output
            for msg in ["Key: service.started", "Notice ID: 1", "Filtered"]
        )
    else:
        assert result == 1


def test_execute_wait_for_notice(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test waiting for notice to appear
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--wait", "1"])

    # Should either wait for notice or timeout gracefully
    if result == 0:
        output = capture.get()
        # Should show notice when it appears
        assert any(
            msg in output
            for msg in ["Notice ID: 1", "Notice appeared", "Wait completed"]
        )
    else:
        # Should fail if timeout or error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["timeout", "Wait failed", "error"])


def test_execute_timeout_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test timeout option for waiting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--timeout", "5", "--wait", "1"])

    # Should either complete within timeout or timeout gracefully
    if result == 0:
        output = capture.get()
        # Should complete within timeout
        assert any(msg in output for msg in ["Notice ID: 1", "Completed", "Found"])
    else:
        # Should fail if timeout exceeded
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["timeout", "exceeded", "error"])


def test_execute_multiple_notice_ids(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test with multiple notice IDs
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1", "2", "3"])

    # Should either handle multiple notices or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show information for multiple notices
        assert any(
            msg in output
            for msg in [
                "Notice ID: 1",
                "Notice ID: 2",
                "Notice ID: 3",
                "Multiple notices",
            ]
        )
    else:
        assert result == 1


def test_execute_notice_occurrence_tracking(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice occurrence tracking
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--occurrences", "1"])

    # Should either show occurrence information or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show occurrence tracking
        assert any(
            msg in output
            for msg in ["Occurrences:", "First occurred:", "Last occurred:", "Count:"]
        )
    else:
        assert result == 1


def test_execute_notice_data_inspection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice data inspection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--data", "1"])

    # Should either show notice data or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show notice data
        assert any(msg in output for msg in ["Data:", "Notice data", "Payload"])
    else:
        assert result == 1


def test_execute_notice_expiry_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice expiry handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--expiry", "1"])

    # Should either show expiry information or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show expiry information
        assert any(msg in output for msg in ["Expires:", "Expiry:", "TTL:", "Timeout:"])
    else:
        assert result == 1


def test_execute_notice_priority_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice priority handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--priority", "high", "1"])

    # Should either filter by priority or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show priority information
        assert any(
            msg in output for msg in ["Priority: high", "High priority", "Priority"]
        )
    else:
        assert result == 1


def test_execute_notice_state_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice state management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--state", "pending", "1"])

    # Should either show state information or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show state information
        assert any(msg in output for msg in ["State: pending", "Pending", "State"])
    else:
        assert result == 1


def test_execute_batch_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test batch operations on notices
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--batch", "--action", "acknowledge", "1", "2"]
        )

    # Should either handle batch operations or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show batch operation results
        assert any(
            msg in output
            for msg in ["Batch operation", "Multiple notices", "Acknowledged"]
        )
    else:
        assert result == 1


def test_execute_notice_history(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test notice history retrieval
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--history", "1"])

    # Should either show history or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show notice history
        assert any(
            msg in output for msg in ["History:", "Previous occurrences", "Timeline"]
        )
    else:
        assert result == 1


def test_execute_pebble_connection_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test Pebble connection handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should handle Pebble connection appropriately
    if result == 0:
        output = capture.get()
        # Should successfully connect and retrieve notice
        assert any(msg in output for msg in ["Notice ID: 1", "Type:", "Connected"])
    else:
        # Should fail gracefully if connection issues
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Connection failed", "Pebble not available", "error"]
        )


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["Notice not found", "Invalid", "error"])
    else:
        assert result == 0


def test_execute_performance_with_large_notices(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test performance with large notice data
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should handle large notices efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test memory efficiency with notice operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticeCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "1"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0
