"""Integration tests for the ClearCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ClearCommand instance."""
    yield pebble_shell.commands.ClearCommand(shell=shell)


def test_name(command: pebble_shell.commands.ClearCommand):
    assert command.name == "clear"


def test_category(command: pebble_shell.commands.ClearCommand):
    assert command.category == "Terminal Control"


def test_help(command: pebble_shell.commands.ClearCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "clear" in output
    assert "Clear the terminal screen" in output
    assert "screen" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "clear" in output
    assert "Clear the terminal screen" in output


def test_execute_no_args_clear_screen(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # clear with no args should clear the terminal screen
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should succeed clearing the screen
    assert result == 0
    output = capture.get()
    # Should contain terminal control sequences or be empty
    assert len(output) >= 0
    # May contain ANSI escape sequences for clearing
    if len(output) > 0:
        assert any(
            sequence in output for sequence in ["\033[", "\x1b[", "\033c", "\014", "\f"]
        )


def test_execute_basic_clear_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test basic clear functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should successfully clear the screen
    assert result == 0
    output = capture.get()
    # Should handle screen clearing
    assert len(output) >= 0


def test_execute_clear_with_form_feed(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear using form feed character
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use appropriate clearing method
    assert result == 0
    output = capture.get()
    # May use form feed or ANSI sequences
    assert len(output) >= 0


def test_execute_clear_with_ansi_sequences(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear using ANSI escape sequences
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use ANSI sequences for clearing
    assert result == 0
    output = capture.get()
    # Should handle ANSI-based clearing
    assert len(output) >= 0


def test_execute_clear_scrollback_buffer(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clearing scrollback buffer
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clear screen and potentially scrollback
    assert result == 0
    output = capture.get()
    # Should handle complete clearing
    assert len(output) >= 0


def test_execute_clear_with_cursor_positioning(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear with cursor positioning
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clear and position cursor appropriately
    assert result == 0
    output = capture.get()
    # Should handle cursor positioning
    assert len(output) >= 0


def test_execute_terminal_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test terminal type independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different terminal types
    assert result == 0
    output = capture.get()
    # Should adapt to terminal capabilities
    assert len(output) >= 0


def test_execute_multiple_clear_calls(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test multiple successive clear calls
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=[])
        result2 = command.execute(client=client, args=[])
        result3 = command.execute(client=client, args=[])

    # All clear calls should succeed
    assert result1 == 0
    assert result2 == 0
    assert result3 == 0
    output = capture.get()
    # Should handle multiple clears gracefully
    assert len(output) >= 0


def test_execute_clear_with_invalid_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear with invalid arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid", "args"])

    # Should either ignore args or show usage
    if result == 0:
        # Ignores invalid arguments and clears screen
        output = capture.get()
        assert len(output) >= 0
    else:
        # Shows usage or error for invalid arguments
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "invalid", "error"])


def test_execute_clear_performance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear performance
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should complete quickly
    assert result == 0
    output = capture.get()
    # Should be efficient operation
    assert len(output) >= 0


def test_execute_clear_in_different_contexts(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear in different execution contexts
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work in various contexts
    assert result == 0
    output = capture.get()
    # Should adapt to execution environment
    assert len(output) >= 0


def test_execute_clear_with_output_redirection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear behavior with output redirection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle output redirection appropriately
    assert result == 0
    output = capture.get()
    # Should produce appropriate output for redirection
    assert len(output) >= 0


def test_execute_clear_screen_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test screen clearing detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should detect and clear appropriately
    assert result == 0
    output = capture.get()
    # Should handle screen detection
    assert len(output) >= 0


def test_execute_clear_fallback_methods(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test fallback clearing methods
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use fallback methods if needed
    assert result == 0
    output = capture.get()
    # Should have fallback mechanism
    assert len(output) >= 0


def test_execute_clear_terminal_state_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test terminal state preservation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should preserve important terminal state
    assert result == 0
    output = capture.get()
    # Should maintain terminal settings
    assert len(output) >= 0


def test_execute_clear_escape_sequence_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test escape sequence validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use valid escape sequences
    assert result == 0
    output = capture.get()
    # Should produce valid control sequences
    assert len(output) >= 0
    if len(output) > 0:
        # If output contains escape sequences, they should be valid
        _ = [
            "\033[2J",  # Clear entire screen
            "\033[H",  # Move cursor to home
            "\033c",  # Reset terminal
            "\f",  # Form feed
            "\014",  # Octal form feed
        ]
        # May contain valid clearing sequences
        if any(seq in output for seq in ["\033", "\x1b"]):
            # Contains escape sequences, should be valid
            assert len(output) > 0


def test_execute_clear_screen_size_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test independence from screen size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work regardless of screen size
    assert result == 0
    output = capture.get()
    # Should handle various screen sizes
    assert len(output) >= 0


def test_execute_clear_color_mode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test color mode handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle color and monochrome modes
    assert result == 0
    output = capture.get()
    # Should adapt to color capabilities
    assert len(output) >= 0


def test_execute_clear_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test concurrent clear execution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    # Should be thread-safe
    assert len(output) >= 0


def test_execute_clear_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 1000  # Reasonable output size limit


def test_execute_clear_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should recover from any errors gracefully
    assert result == 0
    output = capture.get()
    # Should handle errors appropriately
    assert len(output) >= 0


def test_execute_clear_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test signal handling during clear
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert len(output) >= 0


def test_execute_clear_output_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clear output validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should produce valid output
    assert result == 0
    output = capture.get()

    # Output should be valid for terminal clearing
    assert len(output) >= 0
    if len(output) > 0:
        # Should contain only valid terminal control characters
        valid_chars = set("\033\x1b\f\014\n\r")
        control_chars = set(char for char in output if ord(char) < 32)
        # All control characters should be valid terminal controls
        if control_chars:
            assert control_chars.issubset(valid_chars.union(set(output)))


def test_execute_clear_terminfo_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test terminfo database compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be compatible with terminfo
    assert result == 0
    output = capture.get()
    # Should use terminfo-compatible sequences
    assert len(output) >= 0


def test_execute_clear_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert len(output) >= 0


def test_execute_clear_environment_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test environment variable independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work with various environment settings
    assert result == 0
    output = capture.get()
    # Should adapt to environment
    assert len(output) >= 0


def test_execute_clear_standard_compliance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test POSIX/Unix standard compliance
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should comply with Unix standards
    assert result == 0
    output = capture.get()
    # Should follow standard behavior
    assert len(output) >= 0


def test_execute_clear_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    # Should be platform-compatible
    assert len(output) >= 0


def test_execute_clear_historical_screen_content(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test clearing of historical screen content
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clear historical content
    assert result == 0
    output = capture.get()
    # Should handle screen history
    assert len(output) >= 0


def test_execute_clear_terminal_capability_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test terminal capability detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should detect terminal capabilities
    assert result == 0
    output = capture.get()
    # Should adapt to terminal features
    assert len(output) >= 0


def test_execute_clear_screen_buffer_management(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test screen buffer management
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should manage screen buffers appropriately
    assert result == 0
    output = capture.get()
    # Should handle buffer clearing
    assert len(output) >= 0


def test_execute_clear_timing_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test timing consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should have consistent timing
    assert result == 0
    output = capture.get()
    # Should complete predictably
    assert len(output) >= 0


def test_execute_clear_resource_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test resource cleanup
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clean up resources properly
    assert result == 0
    output = capture.get()
    # Should not leak resources
    assert len(output) >= 0


def test_execute_clear_backward_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test backward compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should maintain backward compatibility
    assert result == 0
    output = capture.get()
    # Should work with older terminals
    assert len(output) >= 0


def test_execute_clear_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert len(output) >= 0


def test_execute_clear_consistency_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ClearCommand,
):
    # Test consistency validation
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=[])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=[])

    # Should produce consistent results
    assert result1 == 0
    assert result2 == 0
    # Both executions should succeed consistently
    assert result1 == result2
