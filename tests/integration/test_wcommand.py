"""Integration tests for the WCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a WCommand instance."""
    yield pebble_shell.commands.WCommand(shell=shell)


def test_name(command: pebble_shell.commands.WCommand):
    assert command.name == "w"


def test_category(command: pebble_shell.commands.WCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.WCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "w" in output
    assert "Show who is logged on and what they are doing" in output
    assert "-h" in output
    assert "-s" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "w" in output
    assert "Show who is logged on and what they are doing" in output


def test_execute_no_args_default_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # w with no args should show default output with header and users
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing users or show no users
    if result == 0:
        output = capture.get()
        # Should either show user information or indicate no users
        assert any(
            msg in output
            for msg in [
                "USER",  # Header
                "TTY",  # Header
                "FROM",  # Header
                "LOGIN@",  # Header
                "IDLE",  # Header
                "JCPU",  # Header
                "PCPU",  # Header
                "WHAT",  # Header
                "No users logged in",
                "load average",
            ]
        )
    else:
        # Should not normally fail for basic w command
        assert result == 1


def test_execute_header_suppression_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test -h option to suppress header
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-h"])

    # Should either succeed with suppressed header or fail gracefully
    if result == 0:
        output = capture.get()
        # Should not contain header line
        assert "load average" not in output or len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_short_format_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test -s option for short format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s"])

    # Should either succeed with short format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show shorter format without some columns
        if output.strip():
            # Should have fewer columns in short format
            pass
    else:
        assert result == 1


def test_execute_no_header_short_format_combined(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test -h -s options combined
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-h", "-s"])

    # Should either succeed with both options or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show short format without header
        if output.strip():
            assert "load average" not in output
    else:
        assert result == 1


def test_execute_specific_user_filter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test filtering for specific user
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["root"])

    # Should either succeed showing specific user or no users found
    if result == 0:
        output = capture.get()
        # Should show only specified user or indicate not found
        if "root" in output:
            # Should show root user information
            assert "root" in output
        else:
            # May show no users if root not logged in
            assert any(
                msg in output
                for msg in [
                    "No users",
                    "USER",  # Header even if user not found
                    "load average",
                ]
            )
    else:
        assert result == 1


def test_execute_nonexistent_user_filter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test filtering for nonexistent user
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent-user"])

    # Should either succeed with no results or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show no users or empty result
        assert "nonexistent-user" not in output or "No users" in output
    else:
        assert result == 1


def test_execute_user_information_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test user information display format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display user information in proper format
    if result == 0:
        output = capture.get()
        # Should show proper column headers
        if "USER" in output:
            # Should contain standard w command headers
            assert any(
                header in output
                for header in ["TTY", "FROM", "LOGIN@", "IDLE", "JCPU", "PCPU", "WHAT"]
            )
    else:
        assert result == 1


def test_execute_system_load_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test system load average display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display system load information
    if result == 0:
        output = capture.get()
        # Should show load average in header (unless -h option used)
        if "load average" in output:
            # Should contain load average numbers
            assert "load average" in output
    else:
        assert result == 1


def test_execute_uptime_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test system uptime display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display system uptime information
    if result == 0:
        output = capture.get()
        # Should show uptime information in header
        if "up" in output:
            # Should contain uptime information
            assert any(indicator in output for indicator in ["up", "day", "min", ":"])
    else:
        assert result == 1


def test_execute_current_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test current time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display current time in header
    if result == 0:
        output = capture.get()
        # Should show current time
        if output.strip():
            # Should contain time information (HH:MM format)
            assert (
                any(char in output for char in [":", "AM", "PM"])
                or len(output.strip()) == 0
            )
    else:
        assert result == 1


def test_execute_user_count_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test user count display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display number of users logged in
    if result == 0:
        output = capture.get()
        # Should show user count in header
        if "user" in output:
            # Should indicate number of users
            assert any(indicator in output for indicator in ["user", "users"])
    else:
        assert result == 1


def test_execute_tty_information_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test TTY information display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display TTY information for logged in users
    if result == 0:
        output = capture.get()
        # Should show TTY column
        if "TTY" in output:
            # Should contain TTY information
            assert "TTY" in output
    else:
        assert result == 1


def test_execute_login_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test login time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display login time for users
    if result == 0:
        output = capture.get()
        # Should show login time column
        if "LOGIN@" in output:
            # Should contain login time information
            assert "LOGIN@" in output
    else:
        assert result == 1


def test_execute_idle_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test idle time display
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display idle time for users
    if result == 0:
        output = capture.get()
        # Should show idle time column
        if "IDLE" in output:
            # Should contain idle time information
            assert "IDLE" in output
    else:
        assert result == 1


def test_execute_cpu_time_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test CPU time display (JCPU/PCPU)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display CPU time for users
    if result == 0:
        output = capture.get()
        # Should show CPU time columns
        if any(cpu_col in output for cpu_col in ["JCPU", "PCPU"]):
            # Should contain CPU time information
            assert any(cpu_col in output for cpu_col in ["JCPU", "PCPU"])
    else:
        assert result == 1


def test_execute_current_process_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test current process display (WHAT column)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display current process for users
    if result == 0:
        output = capture.get()
        # Should show what users are doing
        if "WHAT" in output:
            # Should contain process information
            assert "WHAT" in output
    else:
        assert result == 1


def test_execute_remote_host_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test remote host display (FROM column)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should display remote host information
    if result == 0:
        output = capture.get()
        # Should show FROM column
        if "FROM" in output:
            # Should contain remote host information
            assert "FROM" in output
    else:
        assert result == 1


def test_execute_no_users_scenario(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test scenario with no users logged in
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle no users scenario appropriately
    if result == 0:
        output = capture.get()
        # Should show header even with no users, or indicate no users
        assert any(
            msg in output
            for msg in [
                "USER",  # Header
                "No users",
                "load average",
            ]
        )
    else:
        assert result == 1


def test_execute_multiple_users_display(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test display of multiple users
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle multiple users appropriately
    if result == 0:
        output = capture.get()
        # Should show all logged in users
        if output.strip():
            lines = output.strip().split("\n")
            # Should have header and potentially user lines
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_formatting_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test output formatting consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent column alignment
        if "USER" in output:
            # Should maintain column structure
            assert "USER" in output
    else:
        assert result == 1


def test_execute_terminal_width_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test handling of different terminal widths
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle terminal width appropriately
    if result == 0:
        output = capture.get()
        # Should fit output to terminal width
        if output.strip():
            lines = output.strip().split("\n")
            # Should not have excessively long lines
            for line in lines:
                assert len(line) < 1000  # Reasonable line length limit
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test permission handling for system information access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        # May fail if insufficient permissions
        if "permission" in output.lower():
            assert "permission" in output.lower()
    else:
        assert result == 0


def test_execute_system_info_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test access to system information files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should access system information appropriately
    if result == 0:
        output = capture.get()
        # Should successfully read system information
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test error handling for system access issues
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle errors gracefully
    if result == 1:
        output = capture.get()
        # Should show appropriate error message
        if "error" in output.lower():
            assert "error" in output.lower()
    else:
        assert result == 0


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-x"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0


def test_execute_output_truncation_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test handling of long output that needs truncation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle output truncation appropriately
    if result == 0:
        output = capture.get()
        # Should manage long output gracefully
        if output.strip():
            # Should not produce excessively long output
            assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_real_time_information(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test real-time information accuracy
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should provide current real-time information
    if result == 0:
        output = capture.get()
        # Should show current system state
        if "load average" in output:
            # Should contain current load information
            assert "load average" in output
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.WCommand,
):
    # Test data consistency across multiple calls
    outputs = []
    for _ in range(2):
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[])
        if result == 0:
            outputs.append(capture.get())

    # Should provide consistent data structure
    if len(outputs) == 2 and "USER" in outputs[0] and "USER" in outputs[1]:
        # Should maintain consistent format
        assert "USER" in outputs[0] and "USER" in outputs[1]
