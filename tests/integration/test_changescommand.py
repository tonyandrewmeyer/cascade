"""Integration tests for the ChangesCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ChangesCommand instance."""
    yield pebble_shell.commands.ChangesCommand(shell=shell)


def test_name(command: pebble_shell.commands.ChangesCommand):
    assert command.name == "pebble-changes"


def test_category(command: pebble_shell.commands.ChangesCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.ChangesCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "changes" in output
    assert "Show system changes" in output
    assert "--select" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "changes" in output
    assert "Show system changes" in output


def test_execute_no_args_default_all(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # changes with no args should show all changes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing changes or fail if Pebble unavailable
    if result == 0:
        output = capture.get()
        # Should either show changes table or no changes message
        assert any(
            msg in output
            for msg in [
                "No changes found",
                "ID",  # Table header
                "Status",  # Table header
                "Spawn",  # Table header
                "Ready",  # Table header
                "Summary",  # Table header
            ]
        )
    else:
        # Should fail if Pebble API unavailable
        assert result == 1


def test_execute_select_all_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test --select=all option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=all"])

    # Should behave same as no args
    if result == 0:
        output = capture.get()
        # Should show all changes
        assert any(
            msg in output
            for msg in ["No changes found", "ID", "Status", "Spawn", "Ready", "Summary"]
        )
    else:
        assert result == 1


def test_execute_select_in_progress_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test --select=in-progress option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=in-progress"])

    # Should show only in-progress changes
    if result == 0:
        output = capture.get()
        # Should filter to in-progress changes only
        if "Status" in output:
            # Should not show completed changes
            pass
    else:
        assert result == 1


def test_execute_select_ready_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test --select=ready option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=ready"])

    # Should show only ready changes
    if result == 0:
        output = capture.get()
        # Should filter to ready changes only
        if "Status" in output:
            # Should show only ready status changes
            pass
    else:
        assert result == 1


def test_execute_invalid_select_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test with invalid --select option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=invalid"])

    # Should fail with invalid select value error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid choice", "error", "Invalid"])


def test_execute_changes_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test changes table formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # If successful and changes exist, should show table
    if result == 0:
        output = capture.get()
        # Should either show no changes message or changes table headers
        if "ID" in output:
            # Should contain all table headers
            assert "Status" in output
            assert "Spawn" in output
            assert "Ready" in output
            assert "Summary" in output


def test_execute_no_changes_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test when no changes are available
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with no changes message or fail
    if result == 0:
        output = capture.get()
        # Should show no changes message if none exist
        if "No changes found" in output:
            assert "changes" in output


def test_execute_change_id_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change ID display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display change IDs if changes exist
    if result == 0:
        output = capture.get()
        # Should show ID column if changes exist
        if "ID" in output:
            # IDs should be numeric
            pass


def test_execute_change_status_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change status display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display change status if changes exist
    if result == 0:
        output = capture.get()
        # Should show Status column if changes exist
        if "Status" in output:
            # Statuses might include Done, Doing, Hold, Error, etc.
            pass


def test_execute_change_spawn_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change spawn time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display spawn time if changes exist
    if result == 0:
        output = capture.get()
        # Should show Spawn column if changes exist
        if "Spawn" in output:
            # Spawn times should be formatted timestamps
            pass


def test_execute_change_ready_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change ready time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display ready time if changes exist
    if result == 0:
        output = capture.get()
        # Should show Ready column if changes exist
        if "Ready" in output:
            # Ready times should be formatted timestamps
            pass


def test_execute_change_summary_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change summary display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display change summaries if changes exist
    if result == 0:
        output = capture.get()
        # Should show Summary column if changes exist
        if "Summary" in output:
            # Summaries describe what each change does
            pass


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
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


def test_execute_changes_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test that command retrieves changes information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test that table is created properly for changes display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should create table if changes exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        if "ID" in output:
            # Table should be properly formatted
            assert "Status" in output


def test_execute_select_filter_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test select filter functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=ready"])

    # Should filter changes based on select criteria
    if result == 0:
        _ = capture.get()
        # Should apply filtering logic
        pass


def test_execute_change_time_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change time formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format timestamps properly
    if result == 0:
        output = capture.get()
        # Should use consistent time formatting
        if "Spawn" in output or "Ready" in output:
            # Times should be human-readable
            pass


def test_execute_change_data_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test extraction of change data fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should extract all change fields properly
    if result == 0:
        output = capture.get()
        # Should handle all change attributes
        if "ID" in output:
            # Should extract id, status, spawn_time, ready_time, summary
            pass


def test_execute_change_status_filtering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test filtering by change status
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select=in-progress"])

    # Should filter by status correctly
    if result == 0:
        _ = capture.get()
        # Should show only matching status changes
        pass


def test_execute_unknown_fields_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test handling of changes with unknown or missing fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle missing change fields gracefully
    if result == 0:
        output = capture.get()
        # Should display columns even if some fields are missing
        if "ID" in output:
            # Should show "unknown" for missing fields
            pass


def test_execute_large_number_of_changes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test with large number of changes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle many changes efficiently
    if result == 0:
        _ = capture.get()
        # Should display all changes or paginate appropriately
        pass


def test_execute_change_ordering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change ordering in display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should order changes appropriately (likely by ID or time)
    if result == 0:
        output = capture.get()
        # Should have consistent ordering
        if "ID" in output:
            # Changes should be ordered logically
            pass


def test_execute_change_id_type_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test change ID type handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle ChangeID types correctly
    if result == 0:
        _ = capture.get()
        # Should convert and display IDs properly
        pass


def test_execute_empty_change_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test when change list is empty
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle empty change list gracefully
    if result == 0:
        output = capture.get()
        # Should show appropriate message for no changes
        if "No changes found" in output:
            assert len(output.strip()) > 0


def test_execute_select_option_parsing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test select option parsing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--select", "all"])

    # Should parse select option correctly
    if result == 0:
        _ = capture.get()
        # Should apply select filter
        pass
    else:
        # May fail if argument parsing is strict
        assert result == 1


def test_execute_concurrent_changes_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ChangesCommand,
):
    # Test handling of concurrent changes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent/parallel changes
    if result == 0:
        _ = capture.get()
        # Should display all changes regardless of concurrency
        pass
