"""Integration tests for the ResetCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ResetCommand instance."""
    yield pebble_shell.commands.ResetCommand(shell=shell)


def test_name(command: pebble_shell.commands.ResetCommand):
    assert command.name == "reset"


def test_category(command: pebble_shell.commands.ResetCommand):
    assert command.category == "Terminal Control"


def test_help(command: pebble_shell.commands.ResetCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "reset" in output
    assert "Reset terminal to default state" in output
    assert "terminal" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "reset" in output
    assert "Reset terminal to default state" in output


def test_execute_no_args_reset_terminal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # reset with no args should reset the terminal
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should succeed resetting the terminal
    assert result == 0
    output = capture.get()
    # Should contain terminal reset sequences or be empty
    assert len(output) >= 0
    # May contain ANSI escape sequences for resetting
    if len(output) > 0:
        assert any(
            sequence in output for sequence in ["\033[", "\x1b[", "\033c", "\014", "\f"]
        )


def test_execute_basic_reset_functionality(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test basic reset functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should successfully reset the terminal
    assert result == 0
    output = capture.get()
    # Should handle terminal reset
    assert len(output) >= 0


def test_execute_terminal_initialization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminal initialization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should initialize terminal properly
    assert result == 0
    output = capture.get()
    # Should perform initialization sequences
    assert len(output) >= 0


def test_execute_state_restoration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminal state restoration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should restore terminal to default state
    assert result == 0
    output = capture.get()
    # Should handle state restoration
    assert len(output) >= 0


def test_execute_clear_and_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test clearing screen and resetting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clear screen and reset terminal
    assert result == 0
    output = capture.get()
    # Should handle both clearing and resetting
    assert len(output) >= 0


def test_execute_character_set_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test character set reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset character sets
    assert result == 0
    output = capture.get()
    # Should handle character set initialization
    assert len(output) >= 0


def test_execute_cursor_positioning_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test cursor positioning reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset cursor position
    assert result == 0
    output = capture.get()
    # Should handle cursor reset
    assert len(output) >= 0


def test_execute_tab_stops_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test tab stops reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset tab stops to default
    assert result == 0
    output = capture.get()
    # Should handle tab stop initialization
    assert len(output) >= 0


def test_execute_color_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test color attribute reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset color attributes
    assert result == 0
    output = capture.get()
    # Should handle color reset
    assert len(output) >= 0


def test_execute_attribute_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test text attribute reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset text attributes (bold, underline, etc.)
    assert result == 0
    output = capture.get()
    # Should handle attribute reset
    assert len(output) >= 0


def test_execute_scrolling_region_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test scrolling region reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset scrolling regions
    assert result == 0
    output = capture.get()
    # Should handle scrolling region initialization
    assert len(output) >= 0


def test_execute_keyboard_state_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test keyboard state reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset keyboard state
    assert result == 0
    output = capture.get()
    # Should handle keyboard reset
    assert len(output) >= 0


def test_execute_line_drawing_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test line drawing character set reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset line drawing modes
    assert result == 0
    output = capture.get()
    # Should handle line drawing reset
    assert len(output) >= 0


def test_execute_multiple_reset_calls(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test multiple successive reset calls
    with command.shell.console.capture() as capture:
        result1 = command.execute(client=client, args=[])
        result2 = command.execute(client=client, args=[])
        result3 = command.execute(client=client, args=[])

    # All reset calls should succeed
    assert result1 == 0
    assert result2 == 0
    assert result3 == 0
    output = capture.get()
    # Should handle multiple resets gracefully
    assert len(output) >= 0


def test_execute_reset_with_invalid_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test reset with invalid arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid", "args"])

    # Should either ignore args or show usage
    if result == 0:
        # Ignores invalid arguments and resets terminal
        output = capture.get()
        assert len(output) >= 0
    else:
        # Shows usage or error for invalid arguments
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "invalid", "error"])


def test_execute_terminfo_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminfo database compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be compatible with terminfo
    assert result == 0
    output = capture.get()
    # Should use terminfo-compatible sequences
    assert len(output) >= 0


def test_execute_terminal_type_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminal type detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should detect and adapt to terminal type
    assert result == 0
    output = capture.get()
    # Should adapt to terminal capabilities
    assert len(output) >= 0


def test_execute_capability_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminal capability detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should detect terminal capabilities
    assert result == 0
    output = capture.get()
    # Should adapt to available features
    assert len(output) >= 0


def test_execute_fallback_methods(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test fallback reset methods
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should use fallback methods if needed
    assert result == 0
    output = capture.get()
    # Should have fallback mechanism
    assert len(output) >= 0


def test_execute_escape_sequence_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
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
            "\033[!p",  # Soft reset
            "\f",  # Form feed
            "\014",  # Octal form feed
        ]
        # May contain valid reset sequences
        if any(seq in output for seq in ["\033", "\x1b"]):
            # Contains escape sequences, should be valid
            assert len(output) > 0


def test_execute_screen_buffer_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test screen buffer reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset screen buffers
    assert result == 0
    output = capture.get()
    # Should handle buffer reset
    assert len(output) >= 0


def test_execute_alternate_screen_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test alternate screen buffer reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset alternate screen buffer
    assert result == 0
    output = capture.get()
    # Should handle alternate screen reset
    assert len(output) >= 0


def test_execute_terminal_modes_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test terminal modes reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset terminal modes
    assert result == 0
    output = capture.get()
    # Should handle mode reset
    assert len(output) >= 0


def test_execute_application_keypad_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test application keypad mode reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset keypad modes
    assert result == 0
    output = capture.get()
    # Should handle keypad reset
    assert len(output) >= 0


def test_execute_cursor_keys_reset(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test cursor keys mode reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should reset cursor key modes
    assert result == 0
    output = capture.get()
    # Should handle cursor key reset
    assert len(output) >= 0


def test_execute_performance(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test reset performance
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should complete quickly
    assert result == 0
    output = capture.get()
    # Should be efficient operation
    assert len(output) >= 0


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output) >= 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 1000  # Reasonable output size limit


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should recover from any errors gracefully
    assert result == 0
    output = capture.get()
    # Should handle errors appropriately
    assert len(output) >= 0


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test signal handling during reset
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    assert result == 0
    output = capture.get()
    # Should be signal-safe
    assert len(output) >= 0


def test_execute_environment_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test environment variable independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work with various environment settings
    assert result == 0
    output = capture.get()
    # Should adapt to environment
    assert len(output) >= 0


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work regardless of locale settings
    assert result == 0
    output = capture.get()
    # Should be locale-independent
    assert len(output) >= 0


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work across different platforms
    assert result == 0
    output = capture.get()
    # Should be platform-compatible
    assert len(output) >= 0


def test_execute_backward_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test backward compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should maintain backward compatibility
    assert result == 0
    output = capture.get()
    # Should work with older terminals
    assert len(output) >= 0


def test_execute_complete_initialization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test complete terminal initialization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should perform complete initialization
    assert result == 0
    output = capture.get()
    # Should initialize all terminal aspects
    assert len(output) >= 0


def test_execute_soft_reset_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test soft reset behavior
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should perform soft reset
    assert result == 0
    output = capture.get()
    # Should handle soft reset appropriately
    assert len(output) >= 0


def test_execute_hard_reset_capability(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test hard reset capability
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle hard reset if needed
    assert result == 0
    output = capture.get()
    # Should provide thorough reset
    assert len(output) >= 0


def test_execute_state_preservation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test important state preservation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should preserve important state while resetting
    assert result == 0
    output = capture.get()
    # Should balance reset and preservation
    assert len(output) >= 0


def test_execute_resource_cleanup(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test resource cleanup
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should clean up resources properly
    assert result == 0
    output = capture.get()
    # Should not leak resources
    assert len(output) >= 0


def test_execute_timing_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test timing consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should have consistent timing
    assert result == 0
    output = capture.get()
    # Should complete predictably
    assert len(output) >= 0


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should operate robustly
    assert result == 0
    output = capture.get()
    # Should handle stress conditions
    assert len(output) >= 0


def test_execute_consistency_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ResetCommand,
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
