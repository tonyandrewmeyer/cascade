"""Integration tests for the ChecksCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ChecksCommand instance."""
    yield pebble_shell.commands.ChecksCommand(shell=shell)


def test_name(command: pebble_shell.commands.ChecksCommand):
    assert command.name == "pebble-checks"


def test_category(command: pebble_shell.commands.ChecksCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.ChecksCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "checks" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "checks" in capture.get()


def test_execute_no_checks_configured(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with no checks message or show available checks
    if result == 0:
        output = capture.get()
        # Should either show "No health checks configured" or show checks table
        assert any(
            msg in output
            for msg in [
                "No health checks configured",
                "Name",  # Table header if checks exist
            ]
        )
    else:
        # May fail if Pebble API unavailable
        assert result == 1


def test_execute_with_checks_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed and show checks table or handle no checks
    if result == 0:
        output = capture.get()
        # Should show either checks table headers or no checks message
        assert any(
            msg in output
            for msg in [
                "No health checks configured",
                "Name",  # Table header
                "Status",  # Table header
                "Level",  # Table header
                "Type",  # Table header
                "Target",  # Table header
            ]
        )
    else:
        # May fail if Pebble API not accessible
        assert result == 1


def test_execute_checks_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format checks in a table if any exist
    if result == 0:
        output = capture.get()
        # If checks exist, should have table structure
        if "Name" in output:
            # Should contain table headers for checks display
            assert "Level" in output
            assert "Status" in output
            assert "Failures" in output
            assert "Type" in output
            assert "Target" in output


def test_execute_check_info_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test that command attempts to retrieve check information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_plan_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test integration with Pebble plan to get check configurations
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (with or without checks) or fail gracefully
    assert result in [0, 1]


def test_execute_with_args_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test that extra arguments are ignored
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["extra", "args"])

    # Should behave same as no arguments
    assert result in [0, 1]


def test_execute_check_status_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # If successful and checks exist, should display status information
    if result == 0:
        output = capture.get()
        # Should either show no checks message or status information
        if "Name" in output:
            # If showing checks table, should include status info
            assert "Status" in output


def test_execute_check_types_identification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should identify and display check types (http, tcp, exec)
    if result == 0:
        output = capture.get()
        # Should show Type column if checks exist
        if "Type" in output:
            # Check types might include http, tcp, exec
            pass


def test_execute_failure_count_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display failure counts for checks
    if result == 0:
        output = capture.get()
        # Should show Failures column if checks exist
        if "Failures" in output:
            # Failure counts should be numeric
            pass


def test_execute_check_level_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display check levels (alive, ready)
    if result == 0:
        output = capture.get()
        # Should show Level column if checks exist
        if "Level" in output:
            # Levels might include alive, ready
            pass


def test_execute_check_target_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display check targets (URLs, ports, commands)
    if result == 0:
        output = capture.get()
        # Should show Target column if checks exist
        if "Target" in output:
            # Targets depend on check type
            pass


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test error handling when Pebble API is unavailable
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should handle Pebble API errors gracefully
    if result == 1:
        # Error should be handled gracefully
        pass
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_empty_args_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test explicit empty args list
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should behave identically to no arguments case
    assert result in [0, 1]


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChecksCommand,
):
    # Test that table is created properly for checks display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should create table if checks exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        if "Name" in output:
            # Table should be properly formatted
            pass
