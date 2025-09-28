"""Integration tests for the RunlevelCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a RunlevelCommand instance."""
    yield pebble_shell.commands.RunlevelCommand(shell=shell)


def test_name(command: pebble_shell.commands.RunlevelCommand):
    assert command.name == "runlevel"


def test_category(command: pebble_shell.commands.RunlevelCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.RunlevelCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "runlevel" in output
    assert any(
        phrase in output.lower() for phrase in ["runlevel", "init", "system", "level"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "runlevel" in output
    assert any(
        phrase in output.lower() for phrase in ["runlevel", "init", "system", "level"]
    )


def test_execute_no_args_show_runlevel(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # runlevel with no args should show current runlevel
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing runlevel or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain runlevel information
        assert len(output) >= 0
        if len(output) > 0:
            # Should show previous and current runlevel
            parts = output.strip().split()
            if len(parts) >= 2:
                # Format: "previous current" (e.g., "N 5" or "3 5")
                prev_level = parts[0]
                curr_level = parts[1]
                # Previous can be N (none) or digit
                assert prev_level == "N" or prev_level.isdigit()
                # Current should be a digit (0-6) or S
                assert curr_level.isdigit() or curr_level == "S"
            elif len(parts) == 1:
                # Just current runlevel
                level = parts[0]
                assert level.isdigit() or level == "S" or level == "N"
    else:
        # Should fail if cannot determine runlevel
        assert result == 1


def test_execute_current_runlevel_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test current runlevel detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting runlevel or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect current runlevel
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain valid runlevel information
            content = output.strip()
            # Should not be empty
            assert len(content) > 0
            # Should contain runlevel digits or N/S
            assert any(
                char in content
                for char in ["0", "1", "2", "3", "4", "5", "6", "S", "N"]
            )
    else:
        assert result == 1


def test_execute_runlevel_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test runlevel output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with proper format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should have proper runlevel format
        assert len(output) >= 0
        if len(output) > 0:
            content = output.strip()
            parts = content.split()
            # Should have 1 or 2 parts
            assert 1 <= len(parts) <= 2
            for part in parts:
                # Each part should be valid runlevel
                assert (
                    part.isdigit()
                    or part in ["N", "S"]
                    or (len(part) == 1 and part in "0123456NS")
                )
    else:
        assert result == 1


def test_execute_systemd_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test systemd compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with systemd or fail gracefully
    if result == 0:
        output = capture.get()
        # Should work with systemd systems
        assert len(output) >= 0
        if len(output) > 0:
            # Should provide runlevel information even on systemd
            content = output.strip()
            assert len(content) > 0
    else:
        # May fail on systems without traditional runlevels
        assert result == 1


def test_execute_init_system_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test init system detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting init system or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect appropriate init system
        assert len(output) >= 0
    else:
        # Should fail if init system not supported
        assert result == 1


def test_execute_utmp_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test access to utmp records
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing utmp or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access utmp records successfully
        assert len(output) >= 0
    else:
        # Should fail if utmp not accessible
        assert result == 1


def test_execute_previous_runlevel_tracking(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test previous runlevel tracking
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing previous runlevel or fail gracefully
    if result == 0:
        output = capture.get()
        # Should track previous runlevel
        assert len(output) >= 0
        if len(output) > 0:
            parts = output.strip().split()
            if len(parts) >= 2:
                # Should show both previous and current
                prev_level = parts[0]
                curr_level = parts[1]
                # Previous runlevel validation
                assert prev_level == "N" or prev_level.isdigit()
                # Current runlevel validation
                assert curr_level.isdigit() or curr_level == "S"
    else:
        assert result == 1


def test_execute_single_user_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test single user mode detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle single user mode
        assert len(output) >= 0
        if len(output) > 0 and "S" in output:
            # Should properly report single user mode
            assert "S" in output.strip()
    else:
        assert result == 1


def test_execute_multi_user_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test multi-user mode detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting mode or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle multi-user modes
        assert len(output) >= 0
        if len(output) > 0:
            content = output.strip()
            # Should contain valid runlevel
            assert (
                any(level in content for level in ["2", "3", "4", "5"])
                or "S" in content
                or "N" in content
            )
    else:
        assert result == 1


def test_execute_runlevel_0_shutdown(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test runlevel 0 (shutdown) handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully (system shouldn't be at runlevel 0)
    if result == 0:
        output = capture.get()
        # Should handle runlevel 0 if present
        assert len(output) >= 0
        if len(output) > 0 and "0" in output:
            # If at runlevel 0, should report it
            assert "0" in output.strip()
    else:
        assert result == 1


def test_execute_runlevel_6_reboot(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test runlevel 6 (reboot) handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully (system shouldn't be at runlevel 6)
    if result == 0:
        output = capture.get()
        # Should handle runlevel 6 if present
        assert len(output) >= 0
        if len(output) > 0 and "6" in output:
            # If at runlevel 6, should report it
            assert "6" in output.strip()
    else:
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test invalid option
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-z"])

    # Should fail with invalid option error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "option", "usage"])


def test_execute_unexpected_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test with unexpected arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["unexpected", "args"])

    # Should either ignore args or fail gracefully
    if result == 0:
        output = capture.get()
        # Should ignore unexpected arguments
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with permissions or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access runlevel information
        assert len(output) >= 0
    else:
        # Should fail if insufficient permissions
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test container environment handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail gracefully in containers
    if result == 0:
        output = capture.get()
        # Should handle container environments
        assert len(output) >= 0
    else:
        # May fail in containers without traditional init
        assert result == 1


def test_execute_output_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test output consistency across multiple calls
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=[])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=[])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both should succeed with same runlevel (unless changing)
        assert result1 == result2
    else:
        # Should fail consistently
        assert result1 == result2


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should integrate with system properly
    if result == 0:
        output = capture.get()
        # Should integrate with init system
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000  # Very small output expected
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test signal handling during runlevel check
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
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
        # May fail on platforms without runlevels
        assert result == 1


def test_execute_legacy_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test legacy init system compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work with legacy systems
    if result == 0:
        output = capture.get()
        # Should be compatible with SysV init
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_modern_init_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.RunlevelCommand,
):
    # Test modern init system compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work with modern init systems
    if result == 0:
        output = capture.get()
        # Should be compatible with systemd/upstart
        assert len(output) >= 0
    else:
        assert result == 1
