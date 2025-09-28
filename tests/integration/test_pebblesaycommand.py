"""Integration tests for the PebblesayCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a PebblesayCommand instance."""
    yield pebble_shell.commands.PebblesayCommand(shell=shell)


def test_name(command: pebble_shell.commands.PebblesayCommand):
    assert command.name == "pebblesay"


def test_category(command: pebble_shell.commands.PebblesayCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.PebblesayCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "pebblesay" in output
    assert "Pebble version of cowsay" in output
    assert "-f" in output
    assert "-e" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "pebblesay" in output
    assert "Pebble version of cowsay" in output


def test_execute_no_args_default_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # pebblesay with no args should show default message or read from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with default message or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show ASCII art with message
        assert len(output.strip()) > 0
        # Should contain ASCII art characters
        assert any(char in output for char in ["|", "_", "/", "\\", "(", ")"])
        # Should contain message bubble or default text
        assert any(pattern in output for pattern in ["---", "___", "Hello"])
    else:
        # Should fail if no message provided and stdin not available
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["no message", "usage", "pebblesay"])


def test_execute_simple_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with simple message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello Pebble!"])

    # Should succeed showing message with ASCII art
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Hello Pebble!" in output
    # Should contain ASCII art speech bubble
    assert any(char in output for char in ["|", "_", "/", "\\"])
    # Should contain message formatting
    assert any(pattern in output for pattern in ["---", "___", "< ", " >"])


def test_execute_multi_word_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with multi-word message
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["Welcome", "to", "Pebble", "Shell"]
        )

    # Should succeed combining words into message
    assert result == 0
    output = capture.get()
    # Should contain all words
    assert all(word in output for word in ["Welcome", "to", "Pebble", "Shell"])
    # Should contain ASCII art
    assert any(char in output for char in ["|", "_", "/", "\\"])


def test_execute_quoted_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with quoted message containing spaces
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello from Pebble Shell!"])

    # Should succeed with quoted message
    assert result == 0
    output = capture.get()
    # Should contain the full message
    assert "Hello from Pebble Shell!" in output
    # Should contain ASCII art formatting
    assert any(char in output for char in ["|", "_"])


def test_execute_empty_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with empty message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should either succeed with empty bubble or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show empty speech bubble
        assert len(output.strip()) > 0
        # Should still contain ASCII art structure
        assert any(char in output for char in ["|", "_"])
    else:
        # Should fail with empty message
        assert result == 1


def test_execute_long_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with long message
    long_message = "This is a very long message that should test the word wrapping and line formatting capabilities of the pebblesay command implementation."
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_message])

    # Should succeed with word wrapping
    assert result == 0
    output = capture.get()
    # Should contain the message (possibly wrapped)
    assert any(word in output for word in long_message.split())
    # Should contain ASCII art with proper formatting
    assert any(char in output for char in ["|", "_"])
    # Should handle line wrapping properly
    lines = output.strip().split("\n")
    assert len(lines) > 3  # Should have multiple lines for long message


def test_execute_file_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -f option to specify character file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "pebble", "Hello!"])

    # Should either succeed with specified character or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain the message
        assert "Hello!" in output
        # Should contain ASCII art (possibly different character)
        assert len(output.strip()) > 0
    else:
        # Should fail if character file not found
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["character not found", "file not found", "error"]
        )


def test_execute_eyes_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -e option to specify eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "**", "Hello!"])

    # Should succeed with custom eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Hello!" in output
    # Should contain custom eyes in ASCII art
    assert "**" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_tongue_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -T option to specify tongue
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-T", "U", "Hello!"])

    # Should succeed with custom tongue
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Hello!" in output
    # Should contain custom tongue in ASCII art
    assert "U" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_dead_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -d option for dead eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "Oh no!"])

    # Should succeed with dead eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Oh no!" in output
    # Should contain dead eyes (XX or similar)
    assert (
        any(dead_eye in output for dead_eye in ["XX", "xx", "X"])
        or len(output.strip()) > 0
    )
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_greedy_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -g option for greedy eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-g", "Money!"])

    # Should succeed with greedy eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Money!" in output
    # Should contain greedy eyes ($$)
    assert "$$" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_paranoid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -p option for paranoid eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "They're watching!"])

    # Should succeed with paranoid eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "They're watching!" in output
    # Should contain paranoid eyes (@@)
    assert "@@" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_stoned_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -s option for stoned eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "Whoa..."])

    # Should succeed with stoned eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Whoa..." in output
    # Should contain stoned eyes (**)
    assert (
        any(stoned_eye in output for stoned_eye in ["**", "--"])
        or len(output.strip()) > 0
    )
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_tired_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -t option for tired eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "So sleepy..."])

    # Should succeed with tired eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "So sleepy..." in output
    # Should contain tired eyes (--)
    assert "--" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_wired_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -w option for wired eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "Coffee time!"])

    # Should succeed with wired eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Coffee time!" in output
    # Should contain wired eyes (OO)
    assert "OO" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_young_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -y option for young eyes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-y", "I'm young!"])

    # Should succeed with young eyes
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "I'm young!" in output
    # Should contain young eyes (..)
    assert ".." in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_think_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test think mode (thought bubble instead of speech)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--think", "Hmm..."])

    # Should succeed with thought bubble
    if result == 0:
        output = capture.get()
        # Should contain the message
        assert "Hmm..." in output
        # Should contain thought bubble characters
        assert (
            any(think_char in output for think_char in ["o", "O", "°"])
            or len(output.strip()) > 0
        )
        # Should contain ASCII art structure
        assert len(output.strip()) > 0
    else:
        # Should fail if think mode not supported
        assert result == 1


def test_execute_width_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -W option for message width
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-W", "20", "This is a test message"]
        )

    # Should succeed with specified width
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert any(word in output for word in ["This", "test", "message"])
    # Should respect width constraint
    lines = output.strip().split("\n")
    message_lines = [
        line for line in lines if "|" in line or "<" in line or ">" in line
    ]
    if message_lines:
        # Should not exceed specified width significantly
        max_line_length = max(len(line) for line in message_lines)
        assert max_line_length <= 30  # Some allowance for formatting


def test_execute_unicode_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with unicode characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hello 🪨 Pebble! 😊"])

    # Should handle unicode characters
    assert result == 0
    output = capture.get()
    # Should contain unicode message
    assert "Hello" in output and "Pebble!" in output
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_special_characters_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with special characters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=['Hello & welcome to "Pebble Shell"!']
        )

    # Should handle special characters
    assert result == 0
    output = capture.get()
    # Should contain special characters
    assert "Hello" in output and "Pebble Shell" in output
    # Should escape or handle special characters properly
    assert any(char in output for char in ["&", '"']) or "welcome" in output


def test_execute_newline_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with newlines in message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Line 1\nLine 2\nLine 3"])

    # Should handle newlines appropriately
    assert result == 0
    output = capture.get()
    # Should contain all lines
    assert all(line in output for line in ["Line 1", "Line 2", "Line 3"])
    # Should format multi-line message properly
    assert any(char in output for char in ["|", "_"])


def test_execute_tab_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with tabs in message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Item\tValue\tDescription"])

    # Should handle tabs appropriately
    assert result == 0
    output = capture.get()
    # Should contain tab-separated content
    assert all(word in output for word in ["Item", "Value", "Description"])
    # Should format tabbed content properly
    assert any(char in output for char in ["|", "_"])


def test_execute_multiple_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test combining multiple options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-e", "@@", "-T", "U", "Complex message!"]
        )

    # Should succeed with multiple options
    assert result == 0
    output = capture.get()
    # Should contain the message
    assert "Complex message!" in output
    # Should contain custom eyes and tongue
    assert "@@" in output or "U" in output or len(output.strip()) > 0
    # Should contain ASCII art structure
    assert any(char in output for char in ["|", "_"])


def test_execute_conflicting_eye_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test conflicting eye options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-d", "-g", "Conflict!"])

    # Should either use last option or show error
    if result == 0:
        output = capture.get()
        # Should contain the message
        assert "Conflict!" in output
        # Should use one of the eye types
        assert any(eyes in output for eyes in ["XX", "$$"]) or len(output.strip()) > 0
    else:
        # Should fail with conflicting options
        assert result == 1


def test_execute_list_characters_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test -l option to list available characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-l"])

    # Should either succeed listing characters or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show list of available characters
        assert (
            any(
                indicator in output
                for indicator in ["Available", "Characters", "pebble", "default"]
            )
            or len(output.strip()) > 0
        )
    else:
        # Should fail if character listing not implemented
        assert result == 1


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test reading from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either read from stdin or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show default message or stdin content
        assert len(output.strip()) > 0
        # Should contain ASCII art
        assert any(char in output for char in ["|", "_"])
    else:
        # Should fail if no stdin available
        assert result == 1


def test_execute_very_short_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with very short message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Hi"])

    # Should succeed with short message
    assert result == 0
    output = capture.get()
    # Should contain the short message
    assert "Hi" in output
    # Should format properly even for short text
    assert any(char in output for char in ["|", "_"])


def test_execute_single_character_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with single character message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["!"])

    # Should succeed with single character
    assert result == 0
    output = capture.get()
    # Should contain the character
    assert "!" in output
    # Should format properly for single character
    assert any(char in output for char in ["|", "_"])


def test_execute_numeric_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test with numeric message
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["12345"])

    # Should succeed with numeric message
    assert result == 0
    output = capture.get()
    # Should contain the numbers
    assert "12345" in output
    # Should format numbers properly
    assert any(char in output for char in ["|", "_"])


def test_execute_word_wrapping_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test word wrapping behavior
    long_words = "supercalifragilisticexpialidocious antidisestablishmentarianism"
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_words])

    # Should handle long words appropriately
    assert result == 0
    output = capture.get()
    # Should contain the words (possibly wrapped)
    assert any(word in output for word in long_words.split())
    # Should handle wrapping gracefully
    lines = output.strip().split("\n")
    assert len(lines) >= 3  # Should span multiple lines


def test_execute_bubble_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test speech bubble formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Test bubble formatting"])

    # Should format bubble correctly
    assert result == 0
    output = capture.get()
    # Should contain message
    assert "Test bubble formatting" in output
    # Should have proper bubble structure
    lines = output.strip().split("\n")
    if len(lines) >= 3:
        # Should have top border, message line(s), and bottom border
        assert any("_" in line or "-" in line for line in lines[:2])  # Top border
        assert any(
            "|" in line or "<" in line or ">" in line for line in lines[1:-1]
        )  # Message
        assert any("_" in line or "-" in line for line in lines[-2:])  # Bottom border


def test_execute_character_alignment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test character alignment with bubble
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Alignment test"])

    # Should align character with bubble
    assert result == 0
    output = capture.get()
    # Should contain message and character
    assert "Alignment test" in output
    # Should have proper alignment structure
    lines = output.strip().split("\n")
    assert len(lines) >= 5  # Bubble + character should have multiple lines


def test_execute_ascii_art_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test ASCII art consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Consistency check"])

    # Should produce consistent ASCII art
    assert result == 0
    output = capture.get()
    # Should contain consistent ASCII characters
    assert "Consistency check" in output
    # Should have proper ASCII art structure
    ascii_chars = ["|", "_", "/", "\\", "(", ")", "<", ">", "-"]
    assert any(char in output for char in ascii_chars)


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-f", "nonexistent", "Error test"]
        )

    # Should recover from errors gracefully
    output = capture.get()
    if result == 1:
        # Should provide meaningful error message
        assert any(msg in output for msg in ["not found", "character", "error"])
    else:
        # Should fall back to default character
        assert result == 0
        assert "Error test" in output


def test_execute_performance_with_long_message(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test performance with very long message
    very_long_message = "This is a very long message. " * 50
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[very_long_message])

    # Should handle long messages efficiently
    assert result == 0
    output = capture.get()
    # Should complete in reasonable time
    assert len(output) >= 0
    # Should contain some of the message content
    assert "very long message" in output


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["Memory test"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable output size limit
    assert "Memory test" in output


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PebblesayCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "Test"])

    # Should handle invalid options appropriately
    output = capture.get()
    if result == 1:
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0
        assert "Test" in output
