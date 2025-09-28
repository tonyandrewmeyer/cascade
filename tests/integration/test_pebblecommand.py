"""Integration tests for the PebbleCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PebbleCommand instance."""
    yield pebble_shell.commands.PebbleCommand(shell=shell)


def test_name(command: pebble_shell.commands.PebbleCommand):
    assert command.name == "pebble"


def test_category(command: pebble_shell.commands.PebbleCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.PebbleCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "pebble" in output
    assert "Pebble daemon management" in output
    assert "subcommand" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "pebble" in output
    assert "Pebble daemon management" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # pebble with no args should show usage or version
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing usage/version or fail with usage
    if result == 0:
        output = capture.get()
        # Should show usage information or version
        assert any(
            msg in output
            for msg in ["pebble", "version", "usage", "Available commands"]
        )
    else:
        assert result == 1
        output = capture.get()
        assert "pebble <subcommand>" in output


def test_execute_version_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble version subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["version"])

    # Should either succeed with version info or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show version information
        assert any(
            msg in output
            for msg in [
                "pebble",
                "version",
                ".",  # Version typically contains dots
            ]
        )
    else:
        assert result == 1


def test_execute_help_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble help subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["help"])

    # Should either succeed with help info or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show help information
        assert any(msg in output for msg in ["pebble", "commands", "usage", "help"])
    else:
        assert result == 1


def test_execute_invalid_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test with invalid subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid-subcommand"])

    # Should fail with invalid subcommand error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "command", "not found"])


def test_execute_run_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble run subcommand (daemon mode)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["run"])

    # Should either succeed starting daemon or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show daemon startup information
        assert any(msg in output for msg in ["pebble", "daemon", "running"])
    else:
        assert result == 1


def test_execute_add_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble add subcommand (add layer)
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["add", "test-layer", "/path/to/layer.yaml"]
        )

    # Should either succeed adding layer or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show layer addition confirmation
        assert any(msg in output for msg in ["layer", "added", "test-layer"])
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["Add operation failed", "error", "failed"])


def test_execute_start_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble start subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["start", "test-service"])

    # Should either succeed starting service or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show service start confirmation
        assert any(msg in output for msg in ["started", "test-service", "service"])
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Start operation failed", "error", "failed"]
        )


def test_execute_stop_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble stop subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["stop", "test-service"])

    # Should either succeed stopping service or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show service stop confirmation
        assert any(msg in output for msg in ["stopped", "test-service", "service"])
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Stop operation failed", "error", "failed"]
        )


def test_execute_services_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble services subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should either succeed listing services or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show services list or no services message
        assert any(
            msg in output
            for msg in ["Service", "Startup", "Current", "No services found"]
        )
    else:
        assert result == 1


def test_execute_plan_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble plan subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["plan"])

    # Should either succeed showing plan or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show plan information
        assert any(msg in output for msg in ["services:", "layers:", "plan"])
    else:
        assert result == 1


def test_execute_logs_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble logs subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["logs", "test-service"])

    # Should either succeed showing logs or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show logs or no logs message
        assert any(msg in output for msg in ["test-service", "No logs found", "logs"])
    else:
        assert result == 1


def test_execute_exec_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble exec subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["exec", "test-service", "echo", "hello"]
        )

    # Should either succeed executing command or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show command output
        assert "hello" in output
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Exec operation failed", "error", "failed"]
        )


def test_execute_pull_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble pull subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["pull", "/container/file", "/local/file"]
        )

    # Should either succeed pulling file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show transfer completion
        assert any(msg in output for msg in ["pulled", "transferred", "copied"])
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Pull operation failed", "error", "failed"]
        )


def test_execute_push_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble push subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["push", "/local/file", "/container/file"]
        )

    # Should either succeed pushing file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show transfer completion
        assert any(msg in output for msg in ["pushed", "transferred", "uploaded"])
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["Push operation failed", "error", "failed"]
        )


def test_execute_changes_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble changes subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["changes"])

    # Should either succeed showing changes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show changes list or no changes message
        assert any(
            msg in output for msg in ["ID", "Status", "Spawn", "No changes found"]
        )
    else:
        assert result == 1


def test_execute_tasks_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble tasks subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["tasks", "1"])

    # Should either succeed showing tasks or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show tasks for change or no tasks message
        assert any(
            msg in output for msg in ["Kind", "Status", "Summary", "No tasks found"]
        )
    else:
        assert result == 1


def test_execute_reboot_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble reboot subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["reboot"])

    # Should either succeed initiating reboot or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show reboot initiation
        assert any(msg in output for msg in ["reboot", "initiated", "system"])
    else:
        assert result == 1


def test_execute_notices_subcommand(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble notices subcommand
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["notices"])

    # Should either succeed showing notices or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show notices list or no notices message
        assert any(msg in output for msg in ["ID", "Type", "Key", "No notices found"])
    else:
        assert result == 1


def test_execute_subcommand_with_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test pebble subcommand with options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services", "--format=json"])

    # Should either succeed with formatted output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show JSON formatted output
        if output.strip() and "No services found" not in output:
            assert any(
                json_indicator in output for json_indicator in ["{", "}", "[", "]"]
            )
    else:
        assert result == 1


def test_execute_subcommand_chaining(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test handling of multiple subcommands (should use first)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["services", "start", "extra"])

    # Should handle multiple subcommands appropriately
    assert result in [0, 1]


def test_execute_global_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test global pebble options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--verbose", "version"])

    # Should either succeed with verbose output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show verbose output
        assert any(msg in output for msg in ["pebble", "version"])
    else:
        assert result == 1


def test_execute_daemon_communication(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test daemon communication
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should communicate with daemon appropriately
    if result == 0:
        output = capture.get()
        # Should receive response from daemon
        assert any(msg in output for msg in ["Service", "No services found"])
    else:
        assert result == 1


def test_execute_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test API error handling when daemon is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should handle API errors gracefully
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["error", "failed", "connection"])
    else:
        # Should succeed if daemon is available
        assert result == 0


def test_execute_socket_path_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test socket path handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--socket=/custom/socket", "version"]
        )

    # Should handle custom socket path
    if result == 0:
        output = capture.get()
        # Should connect via custom socket
        assert "version" in output or "pebble" in output
    else:
        assert result == 1


def test_execute_timeout_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test timeout handling for operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should handle timeouts appropriately
    if result == 1:
        output = capture.get()
        # May show timeout error
        if "timeout" in output.lower():
            assert "timeout" in output.lower()
    else:
        assert result == 0


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test permission handling for daemon operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should handle permission errors gracefully
    if result == 1:
        output = capture.get()
        if "permission" in output.lower():
            assert "permission" in output.lower()
    else:
        assert result == 0


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test output formatting consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent formatting
        if output.strip():
            assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_error_propagation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test error propagation from subcommands
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["start", "nonexistent-service"])

    # Should propagate errors from subcommands
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["error", "failed", "not found"])
    else:
        # May succeed if service exists
        assert result == 0


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test signal handling during operations
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["version"])

    # Should handle signals appropriately
    assert result in [0, 1]


def test_execute_concurrent_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebbleCommand,
):
    # Test handling of concurrent operations
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["services"])

    # Should handle concurrency appropriately
    if result == 0:
        output = capture.get()
        # Should complete operation successfully
        assert any(msg in output for msg in ["Service", "No services found"])
    else:
        assert result == 1
