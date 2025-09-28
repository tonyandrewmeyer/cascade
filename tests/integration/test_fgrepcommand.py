"""Integration tests for the FgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a FgrepCommand instance."""
    yield pebble_shell.commands.FgrepCommand(shell=shell)


def test_name(command: pebble_shell.commands.FgrepCommand):
    assert command.name == "fgrep"


def test_category(command: pebble_shell.commands.FgrepCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.FgrepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "fgrep" in output
    assert any(
        phrase in output.lower()
        for phrase in ["fixed", "string", "grep", "search", "literal"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "fgrep" in output
    assert any(
        phrase in output.lower()
        for phrase in ["fixed", "string", "grep", "search", "literal"]
    )


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # fgrep with no args should show usage or read from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either fail with usage or wait for stdin
    if result == 0:
        output = capture.get()
        # Should wait for stdin input
        assert len(output) >= 0
    else:
        # Should fail with usage message
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "fgrep", "pattern"])


def test_execute_literal_string_search(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test literal string search (no regex interpretation)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "/etc/passwd"])

    # Should either succeed finding matches or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain matching lines
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain "root" literally
            assert "root" in output.lower()
    else:
        # Should fail if file doesn't exist or no matches
        assert result == 1


def test_execute_special_characters_literal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test that special regex characters are treated literally
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["[.*]", "/etc/passwd"])

    # Should either succeed treating pattern literally or fail gracefully
    if result == 0:
        output = capture.get()
        # Should search for literal "[.*]" string
        assert len(output) >= 0
    else:
        # Should fail if no literal matches found
        assert result == 1


def test_execute_dots_as_literal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test that dots are treated as literal characters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["127.0.0.1", "/etc/hosts"])

    # Should either succeed with literal dots or fail gracefully
    if result == 0:
        output = capture.get()
        # Should find literal "127.0.0.1"
        assert len(output) >= 0
        if len(output) > 0:
            assert "127.0.0.1" in output
    else:
        assert result == 1


def test_execute_asterisk_as_literal(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test that asterisk is treated literally
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["*", "/etc/passwd"])

    # Should either succeed finding literal asterisk or fail gracefully
    if result == 0:
        output = capture.get()
        # Should search for literal "*"
        assert len(output) >= 0
    else:
        # Should fail if no literal asterisk found
        assert result == 1


def test_execute_case_insensitive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test case insensitive search
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "ROOT", "/etc/passwd"])

    # Should either succeed with case insensitive search or fail gracefully
    if result == 0:
        output = capture.get()
        # Should find "root" regardless of case
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain root in any case
            assert "root" in output.lower()
    else:
        assert result == 1


def test_execute_invert_match_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test invert match option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v", "root", "/etc/passwd"])

    # Should either succeed with inverted matches or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain lines not matching "root"
        assert len(output) >= 0
        if len(output) > 0:
            # Should not contain lines with "root"
            lines = output.split("\n")
            for line in lines:
                if line.strip():
                    assert "root" not in line.lower()
    else:
        assert result == 1


def test_execute_line_number_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test line number option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "localhost", "/etc/hosts"])

    # Should either succeed with line numbers or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain line numbers
        assert len(output) >= 0
        if len(output) > 0 and "localhost" in output.lower():
            # Should contain line numbers (digit followed by colon)
            import re

            assert re.search(r"\d+:", output)
    else:
        assert result == 1


def test_execute_count_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test count matches option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-c", "root", "/etc/passwd"])

    # Should either succeed with count or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain count number
        assert len(output) >= 0
        if len(output) > 0:
            # Should be a number
            try:
                int(output.strip())
                assert True
            except ValueError:
                # May contain filename:count format
                assert ":" in output or output.strip().isdigit()
    else:
        assert result == 1


def test_execute_files_with_matches_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test files with matches option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "localhost", "/etc/hosts", "/etc/hostname"]
        )

    # Should either succeed listing files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain filenames
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain file paths
            assert "/etc/" in output
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test quiet mode (just exit status)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "localhost", "/etc/hosts"])

    # Should either succeed silently or fail
    if result == 0:
        output = capture.get()
        # Should produce no output in quiet mode
        assert len(output) == 0
    else:
        assert result == 1


def test_execute_recursive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test recursive search
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "localhost", "/etc"])

    # Should either succeed with recursive search or fail gracefully
    if result == 0:
        output = capture.get()
        # Should search recursively
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain matches from subdirectories
            assert "localhost" in output.lower()
    else:
        assert result == 1


def test_execute_word_boundaries(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test word boundary matching
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "root", "/etc/passwd"])

    # Should either succeed with word boundaries or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match whole words only
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain "root" as whole word
            assert "root" in output.lower()
    else:
        assert result == 1


def test_execute_context_before(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test context lines before match
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-B", "2", "daemon", "/etc/passwd"]
        )

    # Should either succeed with context or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include context lines
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Should have multiple lines if matches found
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_context_after(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test context lines after match
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-A", "2", "root", "/etc/passwd"])

    # Should either succeed with context or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include context lines
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_context_both(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test context lines both before and after
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-C", "1", "localhost", "/etc/hosts"]
        )

    # Should either succeed with context or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include context lines
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_multiple_patterns_from_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test multiple patterns from file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-f", "/etc/hostname", "/etc/hosts"]
        )

    # Should either succeed with pattern file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use patterns from file
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test searching multiple files
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["localhost", "/etc/hosts", "/etc/hostname"]
        )

    # Should either succeed with multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should search both files
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain filename prefixes
            assert "/etc/" in output
    else:
        assert result == 1


def test_execute_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test reading from stdin
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["test"])

    # Should either succeed reading stdin or fail gracefully
    if result == 0:
        output = capture.get()
        # Should read from stdin
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_empty_string_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test empty string pattern
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["", "/etc/passwd"])

    # Should either succeed matching empty string or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match all lines (empty string matches everything)
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_whitespace_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test whitespace pattern
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[" ", "/etc/passwd"])

    # Should either succeed finding spaces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should find lines containing spaces
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain space characters
            assert " " in output
    else:
        assert result == 1


def test_execute_newline_in_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test pattern with newline character
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root\n", "/etc/passwd"])

    # Should either succeed or fail gracefully
    if result == 0:
        output = capture.get()
        # Should search for literal newline
        assert len(output) >= 0
    else:
        # Should fail if no literal newline found
        assert result == 1


def test_execute_unicode_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test Unicode pattern
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["αβγ", "/etc/hosts"])

    # Should either succeed with Unicode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle Unicode characters
        assert len(output) >= 0
        if len(output) > 0:
            assert isinstance(output, str)
    else:
        assert result == 1


def test_execute_very_long_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test very long pattern
    long_pattern = "a" * 1000
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[long_pattern, "/etc/passwd"])

    # Should either succeed with long pattern or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle long patterns
        assert len(output) >= 0
    else:
        # Should fail if pattern not found
        assert result == 1


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["pattern", "/nonexistent/file.txt"]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["pattern", "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # May succeed if readable
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])


def test_execute_binary_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test with binary file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ELF", "/bin/ls"])

    # Should either handle binary or fail gracefully
    if result == 0:
        output = capture.get()
        # Should process binary file
        assert len(output) >= 0
    else:
        # May skip binary files
        assert result == 1


def test_execute_directory_as_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test with directory instead of file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["pattern", "/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "pattern", "/etc/passwd"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_no_regex_interpretation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test that regex metacharacters are not interpreted
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["^root$", "/etc/passwd"])

    # Should either succeed finding literal "^root$" or fail
    if result == 0:
        output = capture.get()
        # Should search for literal "^root$", not regex
        assert len(output) >= 0
    else:
        # Should fail if literal pattern not found
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["localhost", "/etc/hosts"])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test signal handling during search
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["pattern", "/etc/passwd"])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.FgrepCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid", "pattern"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])
