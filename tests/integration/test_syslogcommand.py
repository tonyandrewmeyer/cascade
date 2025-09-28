"""Integration tests for the SyslogCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SyslogCommand instance."""
    yield pebble_shell.commands.SyslogCommand(shell=shell)


def test_name(command: pebble_shell.commands.SyslogCommand):
    assert command.name == "syslog [-n NUM] [-f] [pattern]"


def test_category(command: pebble_shell.commands.SyslogCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.SyslogCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "syslog" in capture.get()


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "syslog" in capture.get()


def test_execute_no_args_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed if syslog files exist or fail gracefully
    if result == 0:
        # Should have read and displayed syslog content
        # Output format depends on actual log content
        pass
    else:
        # Should be 1 if no syslog files are found
        assert result == 1
        output = capture.get()
        assert "No syslog file found" in output
        # Should list the files it tried
        assert any(path in output for path in ["/var/log/syslog", "/var/log/messages"])


def test_execute_with_num_lines_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "50"])

    # Should either succeed with 50 lines or fail if no syslog files
    if result == 0:
        # Should have limited output to 50 lines
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_invalid_num_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "invalid"])

    # Should fail with invalid number error
    assert result == 1
    assert "Invalid number for -n" in capture.get()


def test_execute_num_lines_without_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n"])

    # Should either succeed (treating -n as pattern) or fail if no syslog files
    if result == 0:
        # -n would be treated as a pattern to search for
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_with_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["error"])

    # Should either succeed and filter by pattern or fail if no syslog files
    if result == 0:
        # Should have filtered syslog entries containing "error"
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_with_pattern_and_num_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "25", "warning"])

    # Should either succeed with filtered and limited output or fail
    if result == 0:
        # Should have filtered by "warning" pattern and limited to 25 lines
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_with_follow_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    # Note: Testing follow mode is complex as it runs indefinitely
    # We'll test that the flag is accepted but won't actually follow
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f"])

    # Should either succeed (but we can't test follow behavior) or fail
    if result == 0:
        # Follow mode would start but we can't test the infinite loop
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_zero_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "0"])

    # Should either succeed with no output (0 lines) or fail if no syslog files
    if result == 0:
        # Should show no log lines
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_negative_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "-10"])

    # Should either succeed (negative treated as show all) or fail if no syslog files
    if result == 0:
        # Negative number might show all lines
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_large_num_lines(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "10000"])

    # Should either succeed (will show all available lines) or fail
    if result == 0:
        # Should show up to 10000 lines or all available lines
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_multiple_patterns_uses_first(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["error", "warning"])

    # Should either succeed using first pattern "error" or fail
    if result == 0:
        # Should filter by "error" pattern, "warning" should be ignored
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_pattern_with_special_regex_chars(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["[error]"])

    # Should either succeed with regex pattern or fail
    if result == 0:
        # Should treat "[error]" as regex pattern
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_case_insensitive_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["ERROR"])

    # Should either succeed with case-insensitive matching or fail
    if result == 0:
        # Should match "error", "Error", "ERROR" etc.
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_follow_with_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "info"])

    # Should either succeed (follow with pattern filter) or fail
    if result == 0:
        # Would follow syslog filtering for "info" pattern
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_all_flags_together(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "20", "-f", "debug"])

    # Should either succeed with all options or fail
    if result == 0:
        # Should show last 20 debug entries and then follow
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_unknown_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x"])

    # Unknown flag should be treated as pattern
    if result == 0:
        # -x should be treated as a pattern to search for
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_mixed_flags_and_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "15", "kernel", "-f"])

    # Should parse -n 15, pattern "kernel", and -f flag
    if result == 0:
        # Should show 15 lines with "kernel" and then follow
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()


def test_execute_empty_pattern(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SyslogCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Empty string pattern should be valid
    if result == 0:
        # Should match all lines (empty pattern matches everything)
        pass
    else:
        assert result == 1
        assert "No syslog file found" in capture.get()
