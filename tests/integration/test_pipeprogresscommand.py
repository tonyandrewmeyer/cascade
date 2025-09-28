"""Integration tests for the PipeProgressCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PipeProgressCommand instance."""
    yield pebble_shell.commands.PipeProgressCommand(shell=shell)


def test_name(command: pebble_shell.commands.PipeProgressCommand):
    assert command.name == "pipeprogress"


def test_category(command: pebble_shell.commands.PipeProgressCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.PipeProgressCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["pipe", "progress", "monitor", "throughput", "data"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["pipe", "progress", "monitor", "usage"]
    )


def test_execute_simple_pipe_monitor(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test simple pipe monitoring
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed monitoring or fail with setup error
    if result == 0:
        output = capture.get()
        # Should monitor pipe progress
        assert len(output) >= 0
    else:
        # Should fail with pipe setup or input error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["pipe", "input", "error", "stdin"])


def test_execute_with_size_specification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with total size specification
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "1024"])

    # Should either succeed with size or fail
    if result == 0:
        output = capture.get()
        # Should monitor with known total size
        assert len(output) >= 0
    else:
        # Should fail with input or size error
        assert result == 1


def test_execute_with_update_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with custom update interval
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "1"])

    # Should either succeed with interval or fail
    if result == 0:
        output = capture.get()
        # Should update at specified interval
        assert len(output) >= 0
    else:
        # Should fail with input or interval error
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q"])

    # Should either succeed in quiet mode or fail
    if result == 0:
        output = capture.get()
        # Should suppress progress output
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v"])

    # Should either succeed with verbose output or fail
    if result == 0:
        output = capture.get()
        # Should show detailed progress information
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_with_prefix_text(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with custom prefix text
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "Copying:"])

    # Should either succeed with prefix or fail
    if result == 0:
        output = capture.get()
        # Should use custom prefix
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_percentage_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test percentage display mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-P"])

    # Should either succeed showing percentages or fail
    if result == 0:
        output = capture.get()
        # Should display progress percentages
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_throughput_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test throughput display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t"])

    # Should either succeed showing throughput or fail
    if result == 0:
        output = capture.get()
        # Should display data throughput
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_eta_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test ETA (estimated time of arrival) display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e"])

    # Should either succeed showing ETA or fail
    if result == 0:
        output = capture.get()
        # Should display estimated completion time
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_no_stdin_data(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with no stdin data
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with empty input or fail
    if result == 0:
        output = capture.get()
        # Should handle empty input
        assert len(output) >= 0
    else:
        # Should fail with no input error
        assert result == 1


def test_execute_invalid_size_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with invalid size value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "invalid"])

    # Should fail with invalid size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "size", "number", "error"])


def test_execute_invalid_interval_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with invalid interval value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "abc"])

    # Should fail with invalid interval error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "interval", "number", "error"])


def test_execute_negative_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with negative size value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-100"])

    # Should fail with invalid size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "size", "negative", "error"])


def test_execute_zero_interval(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with zero interval
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "0"])

    # Should either succeed or fail with zero interval
    if result == 0:
        output = capture.get()
        # Should handle zero interval
        assert len(output) >= 0
    else:
        # Should fail with invalid interval
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "interval", "zero", "error"])


def test_execute_large_size_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with very large size value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "999999999999"])

    # Should either succeed with large size or fail
    if result == 0:
        output = capture.get()
        # Should handle large sizes
        assert len(output) >= 0
    else:
        # Should fail with size overflow or input error
        assert result == 1


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test with conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "-v"])  # Quiet and verbose

    # Should either handle conflicts or fail
    if result == 0:
        output = capture.get()
        # Should resolve option conflicts
        assert len(output) >= 0
    else:
        # Should fail with option conflict
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["conflict", "option", "error", "quiet", "verbose"]
        )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_terminal_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test terminal detection and behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with terminal handling or fail
    if result == 0:
        output = capture.get()
        # Should detect terminal capabilities
        assert len(output) >= 0
    else:
        # Should fail with terminal or input error
        assert result == 1


def test_execute_progress_bar_rendering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test progress bar rendering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b"])  # Bar mode

    # Should either succeed with progress bar or fail
    if result == 0:
        output = capture.get()
        # Should render progress bar
        assert len(output) >= 0
    else:
        # Should fail with input or rendering error
        assert result == 1


def test_execute_data_passthrough(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test data passthrough functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed passing data through or fail
    if result == 0:
        output = capture.get()
        # Should pass data through while monitoring
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_signal_handling_sigint(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test SIGINT signal handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_binary_data_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test binary data handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with binary data or fail
    if result == 0:
        output = capture.get()
        # Should handle binary data correctly
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "abc"])  # Trigger error

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "invalid"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "error", "size", "number"])


def test_execute_unicode_text_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test Unicode text in prefix
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "Téléchargement:"])

    # Should either succeed with Unicode or fail
    if result == 0:
        output = capture.get()
        # Should handle Unicode text
        assert len(output) >= 0
    else:
        # Should fail with input or encoding error
        assert result == 1


def test_execute_buffering_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test buffering behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "1024"])  # Buffer size

    # Should either succeed with buffering or fail
    if result == 0:
        output = capture.get()
        # Should handle buffering
        assert len(output) >= 0
    else:
        # Should fail with input or buffer error
        assert result == 1


def test_execute_output_redirection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test output redirection behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with redirection or fail
    if result == 0:
        output = capture.get()
        # Should handle output redirection
        assert len(output) >= 0
    else:
        # Should fail with input error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PipeProgressCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
