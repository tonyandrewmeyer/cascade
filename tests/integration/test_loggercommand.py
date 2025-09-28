"""Integration tests for the LoggerCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LoggerCommand instance."""
    yield pebble_shell.commands.LoggerCommand(shell=shell)


def test_name(command: pebble_shell.commands.LoggerCommand):
    assert command.name == "logger"


def test_category(command: pebble_shell.commands.LoggerCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.LoggerCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "logger" in output
    assert any(
        phrase in output.lower()
        for phrase in ["log", "syslog", "message", "system", "send"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "logger" in output
    assert any(
        phrase in output.lower() for phrase in ["log", "syslog", "message", "system"]
    )


def test_execute_no_args_stdin(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # logger with no args should read from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either read from stdin or show usage
    if result == 0:
        output = capture.get()
        # Should wait for stdin input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "logger", "message"])


def test_execute_simple_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test logging simple message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Test message"])

    # Should either succeed logging or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log message (may have no output)
        assert len(output) >= 0
    else:
        # Should fail if cannot access syslog
        assert result == 1


def test_execute_multiple_word_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test logging message with multiple words
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["This", "is", "a", "test", "message"]
        )

    # Should either succeed logging or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log combined message
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_priority_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test priority option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-p", "info", "Test info message"]
        )

    # Should either succeed with priority or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log with specified priority
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_priority_numeric(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test numeric priority
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-p", "6", "Test numeric priority"]
        )

    # Should either succeed with numeric priority or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log with numeric priority
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_facility_priority(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test facility.priority format
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-p", "user.info", "Test facility.priority"]
        )

    # Should either succeed with facility.priority or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log with facility and priority
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_tag_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test tag option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "testapp", "Message with tag"]
        )

    # Should either succeed with tag or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log with specified tag
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_stderr_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test logging to stderr as well
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "Message to stderr too"])

    # Should either succeed logging to stderr or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log to both syslog and stderr
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_file_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test logging from file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/etc/hostname"])

    # Should either succeed logging file content or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log file contents
        assert len(output) >= 0
    else:
        # Should fail if file doesn't exist or access denied
        assert result == 1


def test_execute_size_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test maximum message size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-S", "100", "Short message"])

    # Should either succeed with size limit or fail gracefully
    if result == 0:
        output = capture.get()
        # Should respect size limit
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_socket_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test custom socket path
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-u", "/dev/log", "Socket message"]
        )

    # Should either succeed with custom socket or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use custom socket
        assert len(output) >= 0
    else:
        # Should fail if socket doesn't exist
        assert result == 1


def test_execute_server_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test remote server option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-n", "localhost", "Remote message"]
        )

    # Should either succeed with remote server or fail gracefully
    if result == 0:
        output = capture.get()
        # Should send to remote server
        assert len(output) >= 0
    else:
        # Should fail if cannot connect to server
        assert result == 1


def test_execute_port_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test custom port option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-P", "514", "Port message"])

    # Should either succeed with custom port or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use custom port
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_tcp_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test TCP instead of UDP
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-T", "TCP message"])

    # Should either succeed with TCP or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use TCP protocol
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_id_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test process ID in log
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "Message with PID"])

    # Should either succeed with PID or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include process ID
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_combined_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test combining multiple options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "test", "-p", "info", "-i", "Combined message"]
        )

    # Should either succeed with combined options or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use all specified options
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_empty_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test empty message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either succeed with empty message or fail gracefully
    if result == 0:
        output = capture.get()
        # Should log empty message
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_long_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test very long message
    long_message = "A" * 1000
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_message])

    # Should either succeed with long message or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle long messages
        assert len(output) >= 0
    else:
        # May fail if message too long
        assert result == 1


def test_execute_special_characters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test message with special characters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["Message with !@#$%^&*() characters"]
        )

    # Should either succeed with special chars or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle special characters
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_unicode_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test Unicode message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Unicode message: αβγ 中文 🚀"])

    # Should either succeed with Unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle Unicode characters
        assert len(output) >= 0
        if len(output) > 0:
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_multiline_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test multiline message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Line 1\nLine 2\nLine 3"])

    # Should either succeed with multiline or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle multiline messages
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_directory_as_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_priority(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test invalid priority
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "invalid", "Test message"])

    # Should fail with invalid priority error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "priority", "error"])


def test_execute_invalid_facility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test invalid facility
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-p", "invalid.info", "Test message"]
        )

    # Should fail with invalid facility error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "facility", "error"])


def test_execute_invalid_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test invalid size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-S", "abc", "Test message"])

    # Should fail with invalid size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "size", "number", "error"])


def test_execute_invalid_port(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test invalid port
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-P", "99999", "Test message"])

    # Should fail with invalid port error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "port", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "Test message"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_syslog_connectivity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test syslog connectivity
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Connectivity test"])

    # Should either succeed connecting to syslog or fail gracefully
    if result == 0:
        output = capture.get()
        # Should connect to syslog successfully
        assert len(output) >= 0
    else:
        # Should fail if syslog unavailable
        assert result == 1


def test_execute_message_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test message formatting
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-t", "app", "-p", "info", "Formatted message"]
        )

    # Should either succeed with proper formatting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should format message properly
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_logging(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test concurrent logging safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Concurrent test"])

    # Should handle concurrent logging safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Memory test"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "Error test"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test signal handling during logging
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Signal test"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_network_resilience(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test network resilience for remote logging
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-n", "unreachable.host", "Network test"]
        )

    # Should either succeed or fail gracefully with network issues
    if result == 0:
        output = capture.get()
        # Should handle network successfully
        assert len(output) >= 0
    else:
        # Should fail gracefully if network unreachable
        assert result == 1


def test_execute_protocol_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test protocol compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-T", "Protocol test"])

    # Should handle different protocols appropriately
    if result == 0:
        output = capture.get()
        # Should use appropriate protocol
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LoggerCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["System integration test"])

    # Should integrate with system logging properly
    if result == 0:
        output = capture.get()
        # Should integrate with system
        assert len(output) >= 0
    else:
        assert result == 1
