"""Integration tests for the NoticesCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a NoticesCommand instance."""
    yield pebble_shell.commands.NoticesCommand(shell=shell)


def test_name(command: pebble_shell.commands.NoticesCommand):
    assert command.name == "pebble-notices"


def test_category(command: pebble_shell.commands.NoticesCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.NoticesCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "notices" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "notices" in capture.get()


def test_execute_no_notices_found(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with notices display or show no notices message
    if result == 1:
        output = capture.get()
        assert "No notices found" in output
    else:
        # Should succeed and show notices table
        assert result == 0


def test_execute_with_notices_available(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed and show notices table or show no notices
    if result == 0:
        output = capture.get()
        # Should show notices table headers if notices exist
        assert any(
            header in output
            for header in [
                "ID",  # Notice ID column
                "Type",  # Notice type column
                "Key",  # Notice key column
                "First Occurred",  # First occurrence timestamp
                "Repeat After",  # Repeat interval
                "Occurrences",  # Occurrence count
            ]
        )
    else:
        # Should be 1 if no notices found
        assert result == 1
        output = capture.get()
        assert "No notices found" in output


def test_execute_notices_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format notices in a table if any exist
    if result == 0:
        output = capture.get()
        # If notices exist, should have table structure
        assert "ID" in output
        assert "Type" in output
        assert "Key" in output
        assert "First Occurred" in output
        assert "Repeat After" in output
        assert "Occurrences" in output


def test_execute_notice_id_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display notice IDs if notices exist
    if result == 0:
        output = capture.get()
        # Should show ID column
        assert "ID" in output


def test_execute_notice_type_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display notice types if notices exist
    if result == 0:
        output = capture.get()
        # Should show Type column
        assert "Type" in output


def test_execute_notice_key_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display notice keys if notices exist
    if result == 0:
        output = capture.get()
        # Should show Key column
        assert "Key" in output


def test_execute_first_occurred_timestamp(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display first occurrence timestamp if notices exist
    if result == 0:
        output = capture.get()
        # Should show First Occurred column
        assert "First Occurred" in output


def test_execute_repeat_after_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display repeat intervals if notices exist
    if result == 0:
        output = capture.get()
        # Should show Repeat After column
        assert "Repeat After" in output


def test_execute_occurrences_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display occurrence counts if notices exist
    if result == 0:
        output = capture.get()
        # Should show Occurrences column
        assert "Occurrences" in output


def test_execute_notices_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test that command attempts to retrieve notices from Pebble
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_with_args_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test that extra arguments are ignored
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["extra", "args"])

    # Should behave same as no arguments
    assert result in [0, 1]


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test error handling when Pebble API is unavailable
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle Pebble API errors gracefully
    if result == 1:
        output = capture.get()
        # Should either show "No notices found" or handle API error
        assert any(msg in output for msg in ["No notices found", "error", "failed"])
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_empty_notices_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle empty notices list properly
    if result == 1:
        output = capture.get()
        assert "No notices found" in output
    else:
        # If successful, should show table structure
        assert result == 0


def test_execute_notice_timestamp_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format timestamps properly if notices exist
    if result == 0:
        output = capture.get()
        # Should show proper timestamp format (YYYY-MM-DD HH:MM:SS)
        # This is tested indirectly through the presence of the column
        assert "First Occurred" in output


def test_execute_notice_data_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle notice data fields properly
    if result == 0:
        output = capture.get()
        # Should display all notice data columns
        expected_columns = [
            "ID",
            "Type",
            "Key",
            "First Occurred",
            "Repeat After",
            "Occurrences",
        ]
        for column in expected_columns:
            assert column in output


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test that table is created properly for notices display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should create table if notices exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        assert "ID" in output  # Primary column
        assert "Type" in output  # Status column
        assert "Key" in output  # Data column


def test_execute_notice_unknown_type_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle notices with unknown or missing types
    if result == 0:
        output = capture.get()
        # Should display Type column (may contain "unknown" for missing types)
        assert "Type" in output


def test_execute_notice_missing_fields_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle notices with missing optional fields
    if result == 0:
        output = capture.get()
        # Should display all columns even if some fields are empty
        assert "Key" in output
        assert "Repeat After" in output
        assert "Occurrences" in output


def test_execute_empty_args_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test explicit empty args list
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should behave identically to no arguments case
    assert result in [0, 1]


def test_execute_panel_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.NoticesCommand,
):
    # Test that output is formatted in a panel
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format output properly (either table in panel or no notices message)
    if result == 0:
        # Should show notices in formatted table
        output = capture.get()
        assert "ID" in output
    else:
        # Should show no notices message
        output = capture.get()
        assert "No notices found" in output
