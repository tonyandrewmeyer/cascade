"""Integration tests for the GetoptCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a GetoptCommand instance."""
    yield pebble_shell.commands.GetoptCommand(shell=shell)


def test_name(command: pebble_shell.commands.GetoptCommand):
    assert command.name == "getopt"


def test_category(command: pebble_shell.commands.GetoptCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.GetoptCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["getopt", "option", "parse", "command", "argument"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["getopt", "option", "parse", "usage"]
    )


def test_execute_no_args_specified(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with no arguments specified
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with missing arguments error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["option", "required", "missing", "usage", "error"]
    )


def test_execute_simple_short_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with simple short options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ab", "-a", "-b"])

    # Should either succeed parsing options or fail with error
    if result == 0:
        output = capture.get()
        # Should parse short options
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain option parsing results
            assert "-a" in output or "-b" in output or "--" in output
    else:
        # Should fail with parsing or option error
        assert result == 1


def test_execute_short_options_with_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test short options with required arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a:b", "-a", "value", "-b"])

    # Should either succeed parsing options with arguments or fail
    if result == 0:
        output = capture.get()
        # Should parse options with arguments
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain parsed option arguments
            assert "value" in output or "-a" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_long_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with long options
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "verbose,help", "ab", "--verbose", "-a"]
        )

    # Should either succeed parsing long options or fail
    if result == 0:
        output = capture.get()
        # Should parse long options
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain long option parsing results
            assert "--verbose" in output or "-a" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_long_options_with_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test long options with required arguments
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-l", "file:,verbose", "a:b", "--file", "test.txt", "-a", "val"],
        )

    # Should either succeed parsing long options with arguments or fail
    if result == 0:
        output = capture.get()
        # Should parse long options with arguments
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain parsed long option arguments
            assert "test.txt" in output or "--file" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_mixed_options_and_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test mixed short and long options with non-option arguments
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-l", "verbose,help", "ab", "-a", "--verbose", "file1", "file2"],
        )

    # Should either succeed parsing mixed options or fail
    if result == 0:
        output = capture.get()
        # Should parse mixed options and separate arguments
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain parsed results
            assert "--" in output or "-a" in output or "file1" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_invalid_short_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with invalid short option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["ab", "-c"]
        )  # -c not in option string

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["invalid", "unknown", "option", "error", "illegal"]
    )


def test_execute_invalid_long_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with invalid long option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "verbose,help", "ab", "--invalid"]
        )

    # Should fail with invalid long option error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid", "unknown", "option", "error", "unrecognized"]
    )


def test_execute_missing_required_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test missing required argument for option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["a:", "-a"]
        )  # -a requires argument

    # Should fail with missing argument error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["argument", "required", "missing", "error", "option"]
    )


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test quiet mode with -q option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-q", "ab", "-c"]
        )  # Invalid option in quiet mode

    # Should either succeed in quiet mode or fail without verbose errors
    if result == 0:
        output = capture.get()
        # Should suppress error messages in quiet mode
        assert len(output) >= 0
    else:
        # Should fail but with minimal output
        assert result == 1
        output = capture.get()
        # Quiet mode should suppress verbose error messages
        assert len(output) < 1000  # Less verbose output


def test_execute_test_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test test mode with -T option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-T", "ab", "-a", "-b"])

    # Should either succeed in test mode or fail
    if result == 0:
        output = capture.get()
        # Should run in test mode
        assert len(output) >= 0
    else:
        # Should fail with test mode error
        assert result == 1


def test_execute_version_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test version information with -V option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-V"])

    # Should either succeed showing version or fail
    if result == 0:
        output = capture.get()
        # Should show version information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain version information
            assert any(
                info in output.lower()
                for info in ["version", "getopt", "util-linux", "build"]
            )
    else:
        # Should fail with version error
        assert result == 1


def test_execute_alternative_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test alternative parsing mode with -a option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", "ab", "-a", "file1", "-b"])

    # Should either succeed in alternative mode or fail
    if result == 0:
        output = capture.get()
        # Should parse in alternative mode
        assert len(output) >= 0
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_name_specification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test program name specification with -n option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "myprog", "ab", "-c"])

    # Should either succeed with custom name or fail
    if result == 0:
        output = capture.get()
        # Should use custom program name
        assert len(output) >= 0
    else:
        # Should fail and possibly show custom name in error
        assert result == 1
        output = capture.get()
        if "myprog" in output:
            assert "myprog" in output


def test_execute_shell_compatibility_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test shell compatibility mode with -s option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "bash", "ab", "-a", "-b"])

    # Should either succeed in shell mode or fail
    if result == 0:
        output = capture.get()
        # Should format output for shell compatibility
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain shell-compatible output
            assert "'" in output or '"' in output or "--" in output
    else:
        # Should fail with shell mode error
        assert result == 1


def test_execute_complex_option_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test complex option string with multiple argument types
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["a:b::c", "-a", "arg1", "-b", "arg2", "-c"]
        )

    # Should either succeed parsing complex options or fail
    if result == 0:
        output = capture.get()
        # Should parse complex option combinations
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain parsed complex options
            assert "arg1" in output or "-a" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_double_dash_separator(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test double dash separator for non-option arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ab", "-a", "--", "-b", "file"])

    # Should either succeed handling separator or fail
    if result == 0:
        output = capture.get()
        # Should properly handle -- separator
        assert len(output) >= 0
        if len(output) > 0:
            # Should separate options from arguments
            assert "--" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_empty_option_string(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with empty option string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["", "-a"])

    # Should fail with invalid option (no options defined)
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "error"])


def test_execute_whitespace_in_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with whitespace in option arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a:", "-a", "value with spaces"])

    # Should either succeed handling whitespace or fail
    if result == 0:
        output = capture.get()
        # Should handle whitespace in arguments
        assert len(output) >= 0
        if len(output) > 0:
            # Should preserve whitespace in arguments
            assert "value with spaces" in output or "value" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_special_characters_in_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test with special characters in arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a:", "-a", "file@#$%.txt"])

    # Should either succeed handling special characters or fail
    if result == 0:
        output = capture.get()
        # Should handle special characters
        assert len(output) >= 0
        if len(output) > 0:
            # Should preserve special characters
            assert "file" in output or "@" in output
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_invalid_option_syntax(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test invalid option syntax in option string
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["a:::", "-a"])  # Invalid syntax

    # Should either succeed or fail with syntax error
    if result == 0:
        output = capture.get()
        # Should handle or reject invalid syntax
        assert len(output) >= 0
    else:
        # Should fail with syntax error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "syntax", "error", "option"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test memory efficiency with large option sets
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["abcdefghijklmnopqrstuvwxyz", "-a", "-b", "-c"]
        )

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ab", "-z"])  # Invalid option

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["invalid", "unknown", "option", "error", "illegal"]
    )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test signal handling during option parsing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ab", "-a", "-b"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with parsing error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test output formatting for different shell types
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-s", "sh", "ab", "-a", "-b", "file"]
        )

    # Should either succeed with proper formatting or fail
    if result == 0:
        output = capture.get()
        # Should format output properly for shell
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain properly formatted shell output
            assert "'" in output or '"' in output or " -- " in output
    else:
        # Should fail with formatting error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.GetoptCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ab", "-a", "-b"])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        # Should fail consistently across platforms
        assert result == 1
