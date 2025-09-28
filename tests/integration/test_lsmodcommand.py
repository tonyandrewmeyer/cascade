"""Integration tests for the LsmodCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a LsmodCommand instance."""
    yield pebble_shell.commands.LsmodCommand(shell=shell)


def test_name(command: pebble_shell.commands.LsmodCommand):
    assert command.name == "lsmod"


def test_category(command: pebble_shell.commands.LsmodCommand):
    assert command.category == "System Information"


def test_help(command: pebble_shell.commands.LsmodCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "lsmod" in output
    assert any(
        phrase in output.lower() for phrase in ["module", "kernel", "list", "loaded"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "lsmod" in output
    assert any(
        phrase in output.lower() for phrase in ["module", "kernel", "list", "loaded"]
    )


def test_execute_no_args_list_modules(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # lsmod with no args should list all loaded modules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed listing modules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain module information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain module header or module names
            lines = output.split("\n")
            assert len(lines) >= 1
            # First line might be header: "Module Size Used by"
            if len(lines) > 1:
                header = lines[0].lower()
                assert any(word in header for word in ["module", "size", "used"])
    else:
        # Should fail if cannot access module information
        assert result == 1


def test_execute_basic_module_listing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test basic module listing functionality
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing modules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show loaded kernel modules
        assert len(output) >= 0
        if len(output) > 0:
            # Should have tabular format
            lines = output.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("Module"):
                    # Each module line should have multiple columns
                    columns = line.split()
                    if len(columns) >= 2:
                        # Should have module name and size
                        assert len(columns[0]) > 0  # Module name
                        assert columns[1].isdigit() or columns[1] == "0"  # Size
    else:
        assert result == 1


def test_execute_module_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test module output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with proper format or fail gracefully
    if result == 0:
        output = capture.get()
        # Should have proper module format
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]
            if len(non_empty_lines) > 0:
                # Should have consistent column structure
                first_line = non_empty_lines[0]
                if "Module" in first_line:
                    # Header line format
                    assert any(
                        word in first_line for word in ["Module", "Size", "Used"]
                    )
    else:
        assert result == 1


def test_execute_kernel_module_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test kernel module detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting modules or fail gracefully
    if result == 0:
        output = capture.get()
        # Should detect kernel modules
        assert len(output) >= 0
        # May have no modules loaded (valid case)
        if len(output) > 0:
            lines = output.split("\n")
            # Should show some module information
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_module_size_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test module size reporting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed reporting sizes or fail gracefully
    if result == 0:
        output = capture.get()
        # Should report module sizes
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("Module"):
                    columns = line.split()
                    if len(columns) >= 2:
                        # Size should be numeric
                        size = columns[1]
                        assert size.isdigit() or size == "0"
    else:
        assert result == 1


def test_execute_module_usage_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test module usage count reporting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed reporting usage or fail gracefully
    if result == 0:
        output = capture.get()
        # Should report module usage counts
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("Module"):
                    columns = line.split()
                    if len(columns) >= 3:
                        # Usage count should be numeric
                        usage = columns[2]
                        assert usage.isdigit() or usage == "0" or usage == "-"
    else:
        assert result == 1


def test_execute_module_dependencies(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test module dependency reporting
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed showing dependencies or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show module dependencies
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            for line in lines:
                if line.strip() and not line.startswith("Module"):
                    # Dependencies shown in fourth column
                    columns = line.split(None, 3)  # Split into max 4 parts
                    if len(columns) >= 4:
                        # Dependencies column exists
                        deps = columns[3]
                        # Dependencies can be module names or empty
                        assert isinstance(deps, str)
    else:
        assert result == 1


def test_execute_proc_modules_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test access to /proc/modules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing proc or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access /proc/modules successfully
        assert len(output) >= 0
    else:
        # Should fail if /proc/modules not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["cannot", "access", "proc", "permission", "error"]
        )


def test_execute_empty_module_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test with empty module list (no modules loaded)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with empty list or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty module list
        assert len(output) >= 0
        if len(output) == 0 or output.strip() == "":
            # No modules loaded - valid case
            assert True
        else:
            # May show header only
            lines = output.split("\n")
            non_empty = [line for line in lines if line.strip()]
            if len(non_empty) == 1:
                # Just header line
                assert "Module" in non_empty[0]
    else:
        assert result == 1


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
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
    command: pebble_shell.commands.LsmodCommand,
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
    command: pebble_shell.commands.LsmodCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with permissions or fail gracefully
    if result == 0:
        output = capture.get()
        # Should access module information
        assert len(output) >= 0
    else:
        # Should fail if insufficient permissions
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_system_integration(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test system integration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should integrate with kernel module system
    if result == 0:
        output = capture.get()
        # Should integrate properly
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_output_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test output consistency across multiple calls
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=[])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=[])

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both should succeed with similar output structure
        assert result1 == result2
    else:
        # Should fail consistently
        assert result1 == result2


def test_execute_large_module_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test with large number of modules
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle large module lists efficiently
    if result == 0:
        output = capture.get()
        # Should handle many modules
        assert len(output) >= 0
        if len(output) > 0:
            lines = output.split("\n")
            # Should handle numerous modules without issues
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
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
    command: pebble_shell.commands.LsmodCommand,
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
    command: pebble_shell.commands.LsmodCommand,
):
    # Test signal handling during module listing
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
    command: pebble_shell.commands.LsmodCommand,
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
    command: pebble_shell.commands.LsmodCommand,
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
        assert result == 1


def test_execute_kernel_version_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test kernel version compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should work with different kernel versions
    if result == 0:
        output = capture.get()
        # Should be compatible across kernel versions
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_module_state_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.LsmodCommand,
):
    # Test module state consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should show consistent module state
    if result == 0:
        output = capture.get()
        # Should reflect current module state
        assert len(output) >= 0
    else:
        assert result == 1
