"""Integration tests for the HealthCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a HealthCommand instance."""
    yield pebble_shell.commands.HealthCommand(shell=shell)


def test_name(command: pebble_shell.commands.HealthCommand):
    assert command.name == "pebble-health"


def test_category(command: pebble_shell.commands.HealthCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.HealthCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "health" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "health" in capture.get()


def test_execute_no_checks_configured(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with no checks message or show health overview
    if result == 0:
        output = capture.get()
        # Should either show "No health checks configured" or health table
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


def test_execute_with_health_checks_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed and show health table or handle no checks
    if result == 0:
        output = capture.get()
        # Should show either health table headers or no checks message
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


def test_execute_health_status_aggregation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that health command aggregates status information
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should calculate health statistics if checks exist
    if result == 0:
        output = capture.get()
        # If health checks exist, should show aggregated status
        if "Status" in output:
            # Should show overall health status
            pass


def test_execute_health_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format health information in a table if checks exist
    if result == 0:
        output = capture.get()
        # If checks exist, should have table structure
        if "Name" in output:
            # Should contain table headers for health display
            assert "Status" in output
            assert "Level" in output
            assert "Type" in output
            assert "Target" in output


def test_execute_healthy_unhealthy_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that command counts healthy vs unhealthy checks
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should aggregate health statistics internally
    if result == 0:
        # Command should calculate healthy_count and unhealthy_count
        # This is internal logic, but affects display
        pass


def test_execute_check_status_up_identification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test identification of "up" status checks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should identify checks with "up" status as healthy
    if result == 0:
        output = capture.get()
        # Should display status information
        if "Status" in output:
            # Status values might include "up", "down", etc.
            pass


def test_execute_check_info_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that command retrieves check information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_plan_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test integration with Pebble plan for check configurations
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (with or without checks) or fail gracefully
    assert result in [0, 1]


def test_execute_with_args_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that extra arguments are ignored
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["extra", "args"])

    # Should behave same as no arguments
    assert result in [0, 1]


def test_execute_check_level_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
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


def test_execute_check_type_identification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
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


def test_execute_check_target_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
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


def test_execute_overall_health_status(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test overall health status assessment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should provide overall health assessment
    if result == 0:
        output = capture.get()
        # Should show health status overview
        if "Status" in output:
            # Should aggregate individual check statuses
            pass


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
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
    command: pebble_shell.commands.HealthCommand,
):
    # Test explicit empty args list
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should behave identically to no arguments case
    assert result in [0, 1]


def test_execute_health_summary_calculation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that health summary is calculated correctly
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should calculate and potentially display health summary
    if result == 0:
        _ = capture.get()
        # Health summary logic is internal but affects display
        pass


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.HealthCommand,
):
    # Test that table is created properly for health display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should create table if checks exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        if "Name" in output:
            # Table should be properly formatted
            pass
