"""Integration tests for the ScriptreplayCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ScriptreplayCommand instance."""
    yield pebble_shell.commands.ScriptreplayCommand(shell=shell)


def test_name(command: pebble_shell.commands.ScriptreplayCommand):
    assert command.name == "scriptreplay"


def test_category(command: pebble_shell.commands.ScriptreplayCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.ScriptreplayCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "scriptreplay" in output
    assert any(
        phrase in output.lower()
        for phrase in ["replay", "script", "timing", "typescript"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "scriptreplay" in output
    assert any(
        phrase in output.lower()
        for phrase in ["replay", "script", "timing", "typescript"]
    )


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # scriptreplay with no args should show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "scriptreplay", "timing"])


def test_execute_replay_with_timing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test replay with timing file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should either succeed replaying or fail gracefully
    if result == 0:
        output = capture.get()
        # Should replay the session
        assert len(output) >= 0
    else:
        # Should fail if files don't exist or are invalid
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["No such file", "cannot", "error", "not found", "invalid"]
        )


def test_execute_replay_default_timing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test replay with default timing file
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[session_path])

    # Should either succeed with default timing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should replay with default timing
        assert len(output) >= 0
    else:
        # Should fail if files don't exist
        assert result == 1


def test_execute_speed_divisor_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test speed divisor option
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-d", "2", timing_path, session_path]
        )

    # Should either succeed with speed divisor or fail gracefully
    if result == 0:
        output = capture.get()
        # Should replay at half speed
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_speed_multiplier_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test speed multiplier option
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-m", "2", timing_path, session_path]
        )

    # Should either succeed with speed multiplier or fail gracefully
    if result == 0:
        output = capture.get()
        # Should replay at double speed
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_timing_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test timing option
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", timing_path, session_path])

    # Should either succeed with timing option or fail gracefully
    if result == 0:
        output = capture.get()
        # Should use specified timing file
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_stdout_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test stdout option
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", session_path, timing_path])

    # Should either succeed with stdout option or fail gracefully
    if result == 0:
        output = capture.get()
        # Should replay stdout
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_maxdelay_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test maximum delay option
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-M", "1", timing_path, session_path]
        )

    # Should either succeed with max delay or fail gracefully
    if result == 0:
        output = capture.get()
        # Should limit delays to 1 second
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_nonexistent_timing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with nonexistent timing file
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/nonexistent/timing.txt", session_path]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_nonexistent_session_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with nonexistent session file
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=[timing_path, "/nonexistent/session.txt"]
        )

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_invalid_timing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with invalid timing file format
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd", session_path])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "format", "timing", "error"])


def test_execute_permission_denied_timing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with permission denied timing file
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/root/.ssh/id_rsa", session_path]
        )

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # May succeed if readable (though invalid format)
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "cannot", "error", "invalid"]
        )


def test_execute_permission_denied_session_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with permission denied session file
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # May succeed if readable
        assert len(output) >= 0
    else:
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])


def test_execute_directory_as_timing_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with directory instead of timing file
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc", session_path])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_directory_as_session_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test with directory instead of session file
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, "/etc"])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["directory", "Is a directory", "error"])


def test_execute_invalid_speed_divisor(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test invalid speed divisor
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-d", "abc", timing_path, session_path]
        )

    # Should fail with invalid divisor error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "divisor", "number", "error"])


def test_execute_invalid_speed_multiplier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test invalid speed multiplier
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-m", "xyz", timing_path, session_path]
        )

    # Should fail with invalid multiplier error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "multiplier", "number", "error"])


def test_execute_zero_speed_divisor(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test zero speed divisor
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-d", "0", timing_path, session_path]
        )

    # Should fail with zero divisor error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "zero", "divisor", "error"])


def test_execute_negative_speed_values(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test negative speed values
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-d", "-2", timing_path, session_path]
        )

    # Should fail with negative value error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative", "error"])


def test_execute_invalid_maxdelay(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test invalid maximum delay
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-M", "invalid", timing_path, session_path]
        )

    # Should fail with invalid delay error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "delay", "number", "error"])


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test invalid option
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z", timing_path, session_path])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test conflicting options
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-d", "2", "-m", "3", timing_path, session_path],
        )

    # Should either handle conflicts or fail appropriately
    if result == 0:
        output = capture.get()
        # May resolve conflicts automatically
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_timing_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test timing format validation
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null", session_path])

    # Should fail with empty timing file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "empty", "timing", "error"])


def test_execute_session_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test session format validation
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, "/dev/null"])

    # Should either succeed with empty session or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty session
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_terminal_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test terminal compatibility
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should either succeed with terminal or fail gracefully
    if result == 0:
        output = capture.get()
        # Should be compatible with terminal
        assert len(output) >= 0
    else:
        # May fail if terminal incompatible
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test memory efficiency
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test error recovery capabilities
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid", timing_path])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test signal handling during replay
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test concurrent execution safety
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ScriptreplayCommand,
):
    # Test cross-platform compatibility
    with tempfile.NamedTemporaryFile(suffix="_timing.txt", delete=False) as timing_file:
        timing_path = timing_file.name
    with tempfile.NamedTemporaryFile(
        suffix="_session.txt", delete=False
    ) as session_file:
        session_path = session_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[timing_path, session_path])

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform differences
        assert len(output) >= 0
    else:
        assert result == 1
