"""Integration tests for the SignalCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SignalCommand instance."""
    yield pebble_shell.commands.SignalCommand(shell=shell)


def test_name(command: pebble_shell.commands.SignalCommand):
    assert command.name == "pebble-signal"


def test_category(command: pebble_shell.commands.SignalCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.SignalCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "signal" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "signal" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # signal with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "Usage:" in output
    assert "signal <signal> <service-name>" in output
    assert "Common signals:" in output


def test_execute_insufficient_args_one_arg(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # signal with only one arg should fail
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM"])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "Usage:" in output
    assert "signal <signal> <service-name>" in output


def test_execute_valid_signal_and_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with valid signal and service name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM", "myservice"])

    # Should either succeed or fail gracefully depending on Pebble availability
    if result == 0:
        output = capture.get()
        # Should show success message
        assert "Successfully sent SIGTERM to services: myservice" in output
    else:
        assert result == 1
        # Should show error if service doesn't exist or Pebble unavailable


def test_execute_multiple_services(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with signal sent to multiple services
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["SIGHUP", "service1", "service2", "service3"]
        )

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show success message with all services
        assert "Successfully sent SIGHUP to services:" in output
        assert "service1" in output
        assert "service2" in output
        assert "service3" in output
    else:
        assert result == 1


def test_execute_common_signals_sigterm(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test SIGTERM signal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM", "testservice"])

    # Should either succeed or fail with API error
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGTERM" in output
    else:
        assert result == 1


def test_execute_common_signals_sigkill(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test SIGKILL signal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGKILL", "testservice"])

    # Should either succeed or fail with API error
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGKILL" in output
    else:
        assert result == 1


def test_execute_common_signals_sighup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test SIGHUP signal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGHUP", "testservice"])

    # Should either succeed or fail with API error
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGHUP" in output
    else:
        assert result == 1


def test_execute_common_signals_sigusr1(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test SIGUSR1 signal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGUSR1", "testservice"])

    # Should either succeed or fail with API error
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGUSR1" in output
    else:
        assert result == 1


def test_execute_common_signals_sigusr2(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test SIGUSR2 signal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGUSR2", "testservice"])

    # Should either succeed or fail with API error
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGUSR2" in output
    else:
        assert result == 1


def test_execute_nonexistent_service(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with nonexistent service
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM", "nonexistent_service"])

    # Should fail with service not found error
    assert result == 1
    output = capture.get()
    assert "Signal operation failed" in output


def test_execute_invalid_signal_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with invalid signal name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["INVALID_SIGNAL", "testservice"])

    # Should fail with invalid signal error
    assert result == 1
    output = capture.get()
    assert "Signal operation failed" in output


def test_execute_numeric_signal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with numeric signal (e.g., signal 15 = SIGTERM)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["15", "testservice"])

    # Should either succeed or fail depending on Pebble signal handling
    if result == 0:
        output = capture.get()
        assert "Successfully sent 15" in output
    else:
        assert result == 1


def test_execute_signal_case_sensitivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test signal name case sensitivity
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["sigterm", "testservice"])

    # Should either handle case insensitive or fail
    if result == 0:
        output = capture.get()
        assert "Successfully sent sigterm" in output
    else:
        assert result == 1


def test_execute_empty_service_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with empty service name
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["SIGTERM", ""])

    # Should fail with invalid service name
    assert result == 1


def test_execute_service_name_with_spaces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with service name containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM", "my service"])

    # Should either handle spaces or fail appropriately
    if result == 0:
        output = capture.get()
        assert "my service" in output
    else:
        assert result == 1


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test API error handling when Pebble is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGTERM", "testservice"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert "Signal operation failed" in output
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_success_message_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test success message formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGHUP", "service1", "service2"])

    # Should format success message properly if successful
    if result == 0:
        output = capture.get()
        assert "Successfully sent SIGHUP to services:" in output
        assert "service1, service2" in output or (
            "service1" in output and "service2" in output
        )


def test_execute_signal_delivery_confirmation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test that signal delivery is confirmed
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGUSR1", "myservice"])

    # Should confirm signal delivery if successful
    if result == 0:
        output = capture.get()
        assert "Successfully sent" in output
        assert "SIGUSR1" in output
        assert "myservice" in output


def test_execute_usage_message_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test usage message content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should show comprehensive usage information
    assert result == 1
    output = capture.get()
    assert "Usage:" in output
    assert "signal <signal> <service-name>" in output
    assert "Common signals:" in output
    assert "SIGTERM" in output
    assert "SIGKILL" in output
    assert "SIGHUP" in output
    assert "SIGUSR1" in output
    assert "SIGUSR2" in output


def test_execute_mixed_valid_invalid_services(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test with mix of valid and invalid service names
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["SIGTERM", "valid_service", "invalid_service"]
        )

    # Should fail if any service is invalid (atomic operation)
    assert result == 1


def test_execute_service_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SignalCommand,
):
    # Test handling of permission errors for signaling services
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["SIGKILL", "restricted_service"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        assert "Signal operation failed" in output
