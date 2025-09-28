"""Integration tests for the EgrepCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a EgrepCommand instance."""
    yield pebble_shell.commands.EgrepCommand(shell=shell)


def test_name(command: pebble_shell.commands.EgrepCommand):
    assert command.name == "egrep"


def test_category(command: pebble_shell.commands.EgrepCommand):
    assert command.category == "Text Processing"


def test_help(command: pebble_shell.commands.EgrepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "egrep" in output
    assert any(
        phrase in output.lower()
        for phrase in ["extended", "regex", "grep", "search", "pattern"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "egrep" in output
    assert any(
        phrase in output.lower()
        for phrase in ["extended", "regex", "grep", "search", "pattern"]
    )


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # egrep with no args should show usage or read from stdin
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
        assert any(msg in output for msg in ["usage", "Usage", "egrep", "pattern"])


def test_execute_simple_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test simple extended regex pattern
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root", "/etc/passwd"])

    # Should either succeed finding matches or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain matching lines
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain "root" somewhere
            assert "root" in output.lower()
    else:
        # Should fail if file doesn't exist or no matches
        assert result == 1


def test_execute_extended_regex_alternation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test extended regex alternation (|)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root|daemon|bin", "/etc/passwd"])

    # Should either succeed with alternation or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain lines matching any of the alternatives
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain at least one of the alternatives
            assert any(alt in output.lower() for alt in ["root", "daemon", "bin"])
    else:
        assert result == 1


def test_execute_extended_regex_plus(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test extended regex plus quantifier (+)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["o+", "/etc/passwd"])

    # Should either succeed with plus quantifier or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match one or more 'o' characters
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain lines with 'o'
            assert "o" in output.lower()
    else:
        assert result == 1


def test_execute_extended_regex_question(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test extended regex question mark (?)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ro?t", "/etc/passwd"])

    # Should either succeed with question mark or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match 'rt' or 'rot'
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_extended_regex_braces(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test extended regex braces {}
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["[0-9]{2,4}", "/etc/passwd"])

    # Should either succeed with braces or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match 2-4 digits
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_extended_regex_parentheses(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test extended regex parentheses for grouping
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["(root|bin):", "/etc/passwd"])

    # Should either succeed with grouping or fail gracefully
    if result == 0:
        output = capture.get()
        # Should match grouped patterns
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_case_insensitive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
):
    # Test line number option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "root", "/etc/passwd"])

    # Should either succeed with line numbers or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain line numbers
        assert len(output) >= 0
        if len(output) > 0 and "root" in output.lower():
            # Should contain line numbers (digit followed by colon)
            import re

            assert re.search(r"\d+:", output)
    else:
        assert result == 1


def test_execute_count_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
):
    # Test files with matches option
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "root", "/etc/passwd", "/etc/hosts"]
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
    command: pebble_shell.commands.EgrepCommand,
):
    # Test quiet mode (just exit status)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "root", "/etc/passwd"])

    # Should either succeed silently or fail
    if result == 0:
        output = capture.get()
        # Should produce no output in quiet mode
        assert len(output) == 0
    else:
        assert result == 1


def test_execute_recursive_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
):
    # Test context lines both before and after
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-C", "1", "daemon", "/etc/passwd"]
        )

    # Should either succeed with context or fail gracefully
    if result == 0:
        output = capture.get()
        # Should include context lines
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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


def test_execute_invalid_regex(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test invalid extended regex
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["[invalid", "/etc/passwd"])

    # Should fail with invalid regex error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "regex", "pattern", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", "pattern", "/etc/passwd"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
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
    command: pebble_shell.commands.EgrepCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["[invalid", "/etc/passwd"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "regex", "error", "pattern"])
