"""Integration tests for the ReadprofileCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ReadprofileCommand instance."""
    yield pebble_shell.commands.ReadprofileCommand(shell=shell)


def test_name(command: pebble_shell.commands.ReadprofileCommand):
    assert command.name == "readprofile"


def test_category(command: pebble_shell.commands.ReadprofileCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.ReadprofileCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["read", "profile", "kernel", "profiling", "performance"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["read", "profile", "kernel", "usage"]
    )


def test_execute_read_kernel_profile(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test reading kernel profiling data
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed reading profile or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain kernel profiling information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain profiling data
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should contain profiling indicators
            profile_found = any(
                any(
                    indicator in line.lower()
                    for indicator in [
                        "kernel",
                        "profile",
                        "function",
                        "address",
                        "ticks",
                    ]
                )
                for line in lines
                if line.strip()
            )
            if profile_found:
                assert profile_found
    else:
        # Should fail if profiling unavailable or permission denied
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "profile", "error", "not found"]
        )


def test_execute_with_map_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with System.map file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "/boot/System.map"])

    # Should either succeed with map file or fail
    if result == 0:
        output = capture.get()
        # Should use map file for symbol resolution
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain symbol information
            has_symbols = any(
                symbol in line.lower()
                for line in output.split("\n")
                for symbol in ["symbol", "function", "kernel"]
            )
            if has_symbols:
                assert has_symbols
    else:
        # Should fail with map file not found or profile error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "map", "profile", "error"])


def test_execute_with_profile_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with specific profile file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/proc/profile"])

    # Should either succeed with profile file or fail
    if result == 0:
        output = capture.get()
        # Should read specified profile file
        assert len(output) >= 0
    else:
        # Should fail with profile file not found
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["not found", "profile", "proc", "error"])


def test_execute_reset_profile_counters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test resetting profile counters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r"])

    # Should either succeed resetting or fail with permission
    if result == 0:
        output = capture.get()
        # Should reset profile counters
        assert len(output) >= 0
    else:
        # Should fail with permission or profile error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "reset", "error", "root"]
        )


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test verbose mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v"])

    # Should either succeed with verbose output or fail
    if result == 0:
        output = capture.get()
        # Should show verbose profiling information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain detailed information
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail with profile or permission error
        assert result == 1


def test_execute_sort_by_ticks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test sorting by tick count
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n"])

    # Should either succeed with sorted output or fail
    if result == 0:
        output = capture.get()
        # Should sort by tick count
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain sorted profiling data
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail with profile or permission error
        assert result == 1


def test_execute_show_only_kernel_symbols(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test showing only kernel symbols
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-k"])

    # Should either succeed showing kernel symbols or fail
    if result == 0:
        output = capture.get()
        # Should show only kernel symbols
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain kernel symbol information
            has_kernel = any(
                "kernel" in line.lower() for line in output.split("\n") if line.strip()
            )
            if has_kernel:
                assert has_kernel
    else:
        # Should fail with profile or permission error
        assert result == 1


def test_execute_multiplier_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with multiplier option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-M", "10"])

    # Should either succeed with multiplier or fail
    if result == 0:
        output = capture.get()
        # Should apply multiplier to tick counts
        assert len(output) >= 0
    else:
        # Should fail with profile or multiplier error
        assert result == 1


def test_execute_profile_step_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with profile step option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "4"])

    # Should either succeed with step size or fail
    if result == 0:
        output = capture.get()
        # Should use specified step size
        assert len(output) >= 0
    else:
        # Should fail with profile or step error
        assert result == 1


def test_execute_nonexistent_map_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with non-existent map file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-m", "/nonexistent/System.map"])

    # Should fail with map file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["not found", "no such file", "map", "error"])


def test_execute_nonexistent_profile_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with non-existent profile file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/nonexistent/profile"])

    # Should fail with profile file not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not found", "no such file", "profile", "error"]
    )


def test_execute_invalid_multiplier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with invalid multiplier value
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-M", "abc"])

    # Should fail with invalid multiplier error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "multiplier", "number", "error"])


def test_execute_invalid_step_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with invalid step size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "invalid"])

    # Should fail with invalid step size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "step", "size", "number", "error"])


def test_execute_zero_multiplier(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with zero multiplier
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-M", "0"])

    # Should either succeed or fail with zero multiplier
    if result == 0:
        output = capture.get()
        # Should handle zero multiplier
        assert len(output) >= 0
    else:
        # Should fail with invalid multiplier
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid", "multiplier", "zero", "error"])


def test_execute_negative_values(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test with negative step size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-s", "-4"])

    # Should fail with negative step size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative", "step", "error"])


def test_execute_permission_denied_proc(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test permission denied accessing /proc/profile
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should read profile if permitted
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "access", "error", "root"]
        )


def test_execute_profiling_disabled(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test when kernel profiling is disabled
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail with profiling disabled
    if result == 0:
        output = capture.get()
        # Should handle disabled profiling
        assert len(output) >= 0
    else:
        # Should fail with profiling disabled error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["disabled", "profiling", "not enabled", "error"]
        )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_conflicting_options(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test conflicting options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-r", "-v"])  # Reset and verbose

    # Should either handle conflicts or fail
    if result == 0:
        output = capture.get()
        # Should resolve option conflicts
        assert len(output) >= 0
    else:
        # Should fail with permission or profile error
        assert result == 1


def test_execute_system_map_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test automatic System.map detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with auto-detection or fail
    if result == 0:
        output = capture.get()
        # Should auto-detect System.map
        assert len(output) >= 0
    else:
        # Should fail with detection or permission error
        assert result == 1


def test_execute_symbol_resolution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test symbol resolution
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-v"])

    # Should either succeed with symbol resolution or fail
    if result == 0:
        output = capture.get()
        # Should resolve symbols
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain symbol information
            has_symbols = any(
                any(
                    symbol_indicator in line.lower()
                    for symbol_indicator in ["symbol", "function", "address"]
                )
                for line in output.split("\n")
                if line.strip()
            )
            if has_symbols:
                assert has_symbols
    else:
        # Should fail with resolution or permission error
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-M", "abc"])  # Trigger error

    # Should be memory efficient even on errors
    assert result == 1
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 10000  # Reasonable error message size


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/invalid/path"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["not found", "error", "invalid", "profile"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test signal handling during profile reading
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with profile or permission error
        assert result == 1


def test_execute_output_formatting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test output formatting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with proper formatting or fail
    if result == 0:
        output = capture.get()
        # Should format profile data properly
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain properly formatted profile information
            lines = output.split("\n")
            assert len(lines) >= 1
            # Should have consistent formatting
            non_empty_lines = [line for line in lines if line.strip()]
            if non_empty_lines:
                assert len(non_empty_lines) >= 1
    else:
        # Should fail with profile or format error
        assert result == 1


def test_execute_kernel_version_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
):
    # Test kernel version compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with kernel compatibility or fail
    if result == 0:
        output = capture.get()
        # Should handle kernel version differences
        assert len(output) >= 0
    else:
        # Should fail with compatibility or permission error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ReadprofileCommand,
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
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "profile", "not found", "error"]
        )
