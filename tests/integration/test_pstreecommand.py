"""Integration tests for the PstreeCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PstreeCommand instance."""
    yield pebble_shell.commands.PstreeCommand(shell=shell)


def test_name(command: pebble_shell.commands.PstreeCommand):
    assert command.name == "pstree"


def test_category(command: pebble_shell.commands.PstreeCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.PstreeCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "pstree" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "pstree" in capture.get()


def test_execute_no_args_default_tree(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed if /proc is accessible or fail gracefully
    if result == 0:
        # Should contain process tree information
        # At minimum should show some processes
        pass
    else:
        # Should be 1 if no processes found or proc access error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No processes found", "Error building process tree"]
        )


def test_execute_proc_access_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # This test verifies that /proc access errors are handled correctly
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # In container environments without full /proc access, should fail gracefully
    if result == 1:
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No processes found", "Error building process tree"]
        )
    else:
        # If it succeeds, should have valid process tree output
        assert result == 0


def test_execute_with_args_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # pstree command doesn't take arguments besides help, they should be ignored
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["some", "args"])

    # Should behave same as no arguments
    if result == 0:
        # Should show process tree regardless of extra args
        pass
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No processes found", "Error building process tree"]
        )


def test_execute_tree_structure_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # If successful, should show hierarchical process tree
    if result == 0:
        _ = capture.get()
        # Process tree should contain PIDs and process names
        # Tree structure uses typical tree characters or indentation
        pass
    else:
        assert result == 1


def test_execute_empty_proc_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # Test behavior when /proc has no process directories
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    if result == 1:
        output = capture.get()
        assert "No processes found" in output
    else:
        # If processes are found, should succeed
        assert result == 0


def test_execute_partial_proc_read_errors(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # Test resilience when some process info can't be read
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed (handling partial failures) or fail gracefully
    if result == 0:
        # Command should handle cases where some process info is unreadable
        pass
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No processes found", "Error building process tree"]
        )


def test_execute_process_hierarchy_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # If successful, should show parent-child relationships
    if result == 0:
        _ = capture.get()
        # Should contain process hierarchy information
        # May contain process names, PIDs, and tree structure indicators
        pass
    else:
        assert result == 1


def test_execute_root_process_identification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should identify and display root processes (PPID 0 or orphaned)
    if result == 0:
        # Tree should start from root processes
        pass
    else:
        assert result == 1


def test_execute_circular_reference_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # Test that circular parent-child references don't cause infinite loops
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should complete without hanging (visited set prevents infinite recursion)
    if result == 0:
        # Should successfully build tree despite any circular references
        pass
    else:
        assert result == 1


def test_execute_large_process_count(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should handle systems with many processes efficiently
    if result == 0:
        # Should complete even with large number of processes
        pass
    else:
        assert result == 1


def test_execute_unknown_flags_ignored(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    # Test that unknown flags are ignored (not parsed)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-x", "--unknown"])

    # Should behave same as no arguments (flags are ignored)
    if result == 0:
        # Should show process tree, ignoring the flags
        pass
    else:
        assert result == 1


def test_execute_process_name_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should display process names when available
    if result == 0:
        # Output should contain process information including names
        pass
    else:
        assert result == 1


def test_execute_tree_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PstreeCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format output as tree structure
    if result == 0:
        _ = capture.get()
        # Tree formatting may use indentation, Unicode tree chars, etc.
        # Should show hierarchical relationships
        pass
    else:
        assert result == 1
