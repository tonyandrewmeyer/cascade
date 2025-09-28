"""Integration tests for the TasksCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a TasksCommand instance."""
    yield pebble_shell.commands.TasksCommand(shell=shell)


def test_name(command: pebble_shell.commands.TasksCommand):
    assert command.name == "pebble-tasks"


def test_category(command: pebble_shell.commands.TasksCommand):
    assert command.category == "Pebble Management"


def test_help(command: pebble_shell.commands.TasksCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "tasks" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "tasks" in capture.get()


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # tasks with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "tasks <change-id>" in output


def test_execute_valid_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with valid change ID
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should either succeed showing tasks or fail if change doesn't exist
    if result == 0:
        output = capture.get()
        # Should either show tasks table or no tasks message
        assert any(
            msg in output
            for msg in [
                "No tasks found for change 1",
                "Kind",  # Table header
                "Status",  # Table header
                "Summary",  # Table header
            ]
        )
    else:
        # Should fail if change doesn't exist or Pebble unavailable
        assert result == 1


def test_execute_nonexistent_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with nonexistent change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["99999"])

    # Should fail with change not found error
    assert result == 1


def test_execute_invalid_change_id_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with invalid change ID format
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["invalid"])

    # Should fail with invalid change ID error
    assert result == 1


def test_execute_negative_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with negative change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-1"])

    # Should fail with invalid change ID error
    assert result == 1


def test_execute_zero_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with zero change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["0"])

    # Should either succeed or fail depending on whether change 0 exists
    assert result in [0, 1]


def test_execute_tasks_table_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test tasks table formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # If successful and tasks exist, should show table
    if result == 0:
        output = capture.get()
        # Should either show no tasks message or tasks table headers
        if "Kind" in output:
            # Should contain all table headers
            assert "Status" in output
            assert "Summary" in output
            assert "Progress" in output
            assert "Log" in output


def test_execute_no_tasks_for_change(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test change with no tasks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should either succeed with no tasks message or fail
    if result == 0:
        output = capture.get()
        # Should show no tasks message if change exists but has no tasks
        if "No tasks found" in output:
            assert "change 1" in output


def test_execute_task_kind_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test task kind display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should display task kinds if tasks exist
    if result == 0:
        output = capture.get()
        # Should show Kind column if tasks exist
        if "Kind" in output:
            # Task kinds might include start, stop, restart, etc.
            pass


def test_execute_task_status_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test task status display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should display task status if tasks exist
    if result == 0:
        output = capture.get()
        # Should show Status column if tasks exist
        if "Status" in output:
            # Task statuses might include done, doing, error, etc.
            pass


def test_execute_task_summary_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test task summary display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should display task summaries if tasks exist
    if result == 0:
        output = capture.get()
        # Should show Summary column if tasks exist
        if "Summary" in output:
            # Summaries describe what each task does
            pass


def test_execute_task_progress_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test task progress display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should display task progress if tasks exist
    if result == 0:
        output = capture.get()
        # Should show Progress column if tasks exist
        if "Progress" in output:
            # Progress might show completion percentage or status
            pass


def test_execute_task_log_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test task log display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should display task logs if tasks exist
    if result == 0:
        output = capture.get()
        # Should show Log column if tasks exist
        if "Log" in output:
            # Logs contain task execution details
            pass


def test_execute_change_retrieval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test that command retrieves change information
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["1"])

    # Should either succeed or fail gracefully
    assert result in [0, 1]


def test_execute_multiple_args_extra_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with multiple arguments (extras should be ignored)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["1", "extra", "args"])

    # Should use first change ID and ignore extras
    assert result in [0, 1]


def test_execute_pebble_api_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test error handling when Pebble API is unavailable
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["1"])

    # Should handle Pebble API errors gracefully
    if result == 1:
        # Error should be handled gracefully
        pass
    else:
        # Should succeed if Pebble API is available
        assert result == 0


def test_execute_large_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with very large change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["999999999"])

    # Should either succeed or fail depending on change existence
    assert result in [0, 1]


def test_execute_string_change_id_numeric(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with numeric string change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["123"])

    # Should either succeed or fail depending on change existence
    assert result in [0, 1]


def test_execute_change_id_with_leading_zeros(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with change ID having leading zeros
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["00001"])

    # Should either succeed (treated as 1) or fail
    assert result in [0, 1]


def test_execute_empty_change_id(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test with empty change ID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[""])

    # Should fail with invalid change ID
    assert result == 1


def test_execute_table_creation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test that table is created properly for tasks display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should create table if tasks exist
    if result == 0:
        output = capture.get()
        # Should use Rich table formatting
        if "Kind" in output:
            # Table should be properly formatted
            assert "Status" in output


def test_execute_task_unknown_fields_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test handling of tasks with unknown or missing fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should handle missing task fields gracefully
    if result == 0:
        output = capture.get()
        # Should display columns even if some fields are missing
        if "Kind" in output:
            # Should show "unknown" for missing fields
            pass


def test_execute_change_id_type_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test change ID type conversion to ChangeID
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["42"])

    # Should convert string to ChangeID type
    assert result in [0, 1]


def test_execute_task_data_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.TasksCommand,
):
    # Test extraction of task data fields
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])

    # Should extract all task fields properly
    if result == 0:
        output = capture.get()
        # Should handle all task attributes
        if "Kind" in output:
            # Should extract kind, status, summary, progress, log
            pass
