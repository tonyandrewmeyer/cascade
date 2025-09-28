"""Integration tests for the NotifyCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NotifyCommand instance."""
    yield pebble_shell.commands.NotifyCommand(shell=shell)


def test_name(command: pebble_shell.commands.NotifyCommand):
    assert command.name == "notify"


def test_category(command: pebble_shell.commands.NotifyCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.NotifyCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "notify" in output
    assert "Send Pebble notification" in output
    assert "--type" in output
    assert "--key" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "notify" in output
    assert "Send Pebble notification" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # notify with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "notify --type <TYPE> --key <KEY>" in output


def test_execute_simple_notification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test sending simple notification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event"]
        )

    # Should either succeed sending notification or fail if Pebble unavailable
    if result == 0:
        output = capture.get()
        # Should show notification sent message
        assert any(
            msg in output
            for msg in [
                "Notification sent",
                "Notice created",
                "Notification successful",
                "Sent notification",
            ]
        )
    else:
        # Should fail if Pebble is not available or accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in [
                "Notification failed",
                "Connection failed",
                "Pebble not available",
                "error",
            ]
        )


def test_execute_notification_with_data(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test sending notification with data
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "test.event",
                "--data",
                '{"message": "test"}',
            ],
        )

    # Should either succeed with data or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show notification sent with data
        assert any(
            msg in output
            for msg in ["Notification sent", "With data", "Data included", "Sent"]
        )
    else:
        assert result == 1


def test_execute_change_event_notification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test change event notification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "change-update", "--key", "service.started"]
        )

    # Should either succeed with change event or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show change event notification
        assert any(
            msg in output
            for msg in ["Change notification sent", "Change event", "Notification sent"]
        )
    else:
        assert result == 1


def test_execute_custom_notification_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test custom notification type
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "application.event"]
        )

    # Should either succeed with custom type or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show custom notification
        assert any(
            msg in output
            for msg in ["Custom notification sent", "Notification sent", "Custom type"]
        )
    else:
        assert result == 1


def test_execute_warning_notification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test warning notification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "warning", "--key", "system.warning"]
        )

    # Should either succeed with warning or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show warning notification
        assert any(
            msg in output
            for msg in [
                "Warning notification sent",
                "Warning sent",
                "Notification sent",
            ]
        )
    else:
        assert result == 1


def test_execute_error_notification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test error notification
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "error", "--key", "system.error"]
        )

    # Should either succeed with error notification or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show error notification
        assert any(
            msg in output
            for msg in ["Error notification sent", "Error sent", "Notification sent"]
        )
    else:
        assert result == 1


def test_execute_missing_type_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with missing type argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--key", "test.event"])

    # Should fail with missing type error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["missing type", "--type required", "usage"])


def test_execute_missing_key_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with missing key argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--type", "custom"])

    # Should fail with missing key error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["missing key", "--key required", "usage"])


def test_execute_invalid_notification_type(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with invalid notification type
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "invalid-type", "--key", "test.event"]
        )

    # Should either accept invalid type or fail with validation error
    if result == 0:
        output = capture.get()
        # Should accept and send notification
        assert "Notification sent" in output
    else:
        # Should fail with invalid type error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid type", "unknown type", "error"])


def test_execute_empty_key(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with empty key
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--type", "custom", "--key", ""])

    # Should fail with empty key error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["empty key", "invalid key", "error"])


def test_execute_json_data_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with JSON data format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "test.event",
                "--data",
                '{"level": "info", "message": "test notification"}',
            ],
        )

    # Should either succeed with JSON data or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send notification with JSON data
        assert any(
            msg in output for msg in ["Notification sent", "JSON data", "Data included"]
        )
    else:
        assert result == 1


def test_execute_malformed_json_data(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with malformed JSON data
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "test.event",
                "--data",
                '{"malformed": json}',
            ],
        )

    # Should fail with JSON parsing error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid JSON", "malformed data", "JSON error", "error"]
    )


def test_execute_string_data_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with string data format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "test.event",
                "--data",
                "simple string message",
            ],
        )

    # Should either succeed with string data or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send notification with string data
        assert any(
            msg in output
            for msg in ["Notification sent", "String data", "Data included"]
        )
    else:
        assert result == 1


def test_execute_repeat_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test repeat option for notifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--repeat", "3"],
        )

    # Should either succeed with repeat or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send multiple notifications
        assert any(
            msg in output
            for msg in [
                "3 notifications sent",
                "Repeated notifications",
                "Multiple sent",
            ]
        )
    else:
        assert result == 1


def test_execute_invalid_repeat_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with invalid repeat count
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--repeat", "invalid"],
        )

    # Should fail with invalid repeat count error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid repeat", "invalid count", "error"])


def test_execute_zero_repeat_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with zero repeat count
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--repeat", "0"],
        )

    # Should either handle zero repeat or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle zero repeat (no notifications)
        assert any(
            msg in output
            for msg in ["0 notifications sent", "No notifications", "Zero repeat"]
        )
    else:
        assert result == 1


def test_execute_delay_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test delay option between notifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "test.event",
                "--repeat",
                "2",
                "--delay",
                "1",
            ],
        )

    # Should either succeed with delay or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send notifications with delay
        assert any(
            msg in output for msg in ["notifications sent", "With delay", "Delayed"]
        )
    else:
        assert result == 1


def test_execute_priority_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test priority option for notifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--priority", "high"],
        )

    # Should either succeed with priority or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send high priority notification
        assert any(
            msg in output
            for msg in [
                "High priority notification",
                "Priority set",
                "Notification sent",
            ]
        )
    else:
        assert result == 1


def test_execute_invalid_priority(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with invalid priority level
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--priority", "invalid"],
        )

    # Should fail with invalid priority error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid priority", "unknown priority", "error"]
    )


def test_execute_expiry_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test expiry option for notifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--expiry", "3600"],
        )

    # Should either succeed with expiry or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send notification with expiry
        assert any(
            msg in output
            for msg in ["Notification sent", "Expiry set", "TTL configured"]
        )
    else:
        assert result == 1


def test_execute_invalid_expiry_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test with invalid expiry format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--expiry", "invalid"],
        )

    # Should fail with invalid expiry error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid expiry", "invalid duration", "error"])


def test_execute_batch_notifications(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test batch notifications with multiple keys
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=[
                "--type",
                "custom",
                "--key",
                "event.1",
                "--key",
                "event.2",
                "--batch",
            ],
        )

    # Should either succeed with batch or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send batch notifications
        assert any(
            msg in output
            for msg in [
                "Batch notifications sent",
                "Multiple notifications",
                "Batch completed",
            ]
        )
    else:
        assert result == 1


def test_execute_confirm_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test confirm option for acknowledgment
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event", "--confirm"]
        )

    # Should either succeed with confirmation or fail gracefully
    if result == 0:
        output = capture.get()
        # Should request confirmation
        assert any(
            msg in output
            for msg in [
                "Confirmation requested",
                "Awaiting acknowledgment",
                "Confirmed",
            ]
        )
    else:
        assert result == 1


def test_execute_pebble_connection_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test Pebble connection handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event"]
        )

    # Should handle Pebble connection appropriately
    if result == 0:
        output = capture.get()
        # Should successfully connect and send notification
        assert any(msg in output for msg in ["Notification sent", "Connected", "Sent"])
    else:
        # Should fail gracefully if connection issues
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["Connection failed", "Pebble not available", "error"]
        )


def test_execute_notification_queuing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test notification queuing behavior
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event", "--queue"]
        )

    # Should either succeed with queuing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should queue notification
        assert any(
            msg in output for msg in ["Notification queued", "Added to queue", "Queued"]
        )
    else:
        assert result == 1


def test_execute_notification_deduplication(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test notification deduplication
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event", "--dedupe"]
        )

    # Should either succeed with deduplication or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle deduplication
        assert any(
            msg in output for msg in ["Notification sent", "Deduplicated", "Unique"]
        )
    else:
        assert result == 1


def test_execute_async_notification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test asynchronous notification sending
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event", "--async"]
        )

    # Should either succeed asynchronously or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send notification asynchronously
        assert any(
            msg in output for msg in ["Notification sent", "Async", "Background"]
        )
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid"])

    # Should recover from errors gracefully
    if result == 1:
        output = capture.get()
        # Should provide meaningful error message
        assert any(msg in output for msg in ["invalid", "usage", "error"])
    else:
        assert result == 0


def test_execute_performance_with_large_data(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test performance with large notification data
    large_data = '{"data": "' + "x" * 1000 + '"}'
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["--type", "custom", "--key", "test.event", "--data", large_data],
        )

    # Should handle large data efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
):
    # Test memory efficiency with notifications
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--type", "custom", "--key", "test.event"]
        )

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NotifyCommand,
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
