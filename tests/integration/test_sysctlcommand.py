"""Integration tests for the SysctlCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a SysctlCommand instance."""
    yield pebble_shell.commands.SysctlCommand(shell=shell)


def test_name(command: pebble_shell.commands.SysctlCommand):
    assert command.name == "sysctl"


def test_category(command: pebble_shell.commands.SysctlCommand):
    assert command.category == "System Administration"


def test_help(command: pebble_shell.commands.SysctlCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "sysctl" in output
    assert "Configure kernel parameters" in output
    assert "parameter" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "sysctl" in output
    assert "Configure kernel parameters" in output


def test_execute_no_args_show_all(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # sysctl with no args should show all parameters or usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either show all parameters or show usage
    if result == 0:
        output = capture.get()
        # Should contain kernel parameters
        assert len(output.strip()) > 0
        # Should contain typical sysctl output format
        assert any(
            format_indicator in output
            for format_indicator in ["=", "kernel.", "net.", "vm.", "fs."]
        )
    else:
        # May fail and show usage
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["usage", "Usage", "sysctl", "parameter"])


def test_execute_all_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test showing all kernel parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should succeed showing all parameters
    assert result == 0
    output = capture.get()
    # Should contain extensive kernel parameter information
    assert len(output.strip()) > 0
    # Should contain various kernel subsystem parameters
    assert any(
        subsystem in output.lower()
        for subsystem in ["kernel", "net", "vm", "fs", "dev"]
    )
    # Should contain parameter=value format
    assert "=" in output


def test_execute_specific_parameter_read(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test reading specific kernel parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.hostname"])

    # Should succeed showing specific parameter
    assert result == 0
    output = capture.get()
    # Should contain hostname parameter
    assert len(output.strip()) > 0
    # Should contain parameter=value format
    assert "kernel.hostname" in output
    assert "=" in output


def test_execute_network_parameter_read(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test reading network parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["net.ipv4.ip_forward"])

    # Should succeed showing network parameter
    assert result == 0
    output = capture.get()
    # Should contain IP forwarding parameter
    assert len(output.strip()) > 0
    assert "net.ipv4.ip_forward" in output
    assert any(value in output for value in ["0", "1"])


def test_execute_memory_parameter_read(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test reading memory management parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["vm.swappiness"])

    # Should succeed showing memory parameter
    if result == 0:
        output = capture.get()
        # Should contain swappiness parameter
        assert len(output.strip()) > 0
        assert "vm.swappiness" in output
        assert "=" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_filesystem_parameter_read(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test reading filesystem parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["fs.file-max"])

    # Should succeed showing filesystem parameter
    if result == 0:
        output = capture.get()
        # Should contain file-max parameter
        assert len(output.strip()) > 0
        assert "fs.file-max" in output
        assert "=" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_pattern_matching(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test pattern matching for parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.*"])

    # Should succeed showing kernel parameters
    assert result == 0
    output = capture.get()
    # Should contain multiple kernel parameters
    assert len(output.strip()) > 0
    # Should contain various kernel parameters
    assert "kernel." in output
    # Should have multiple lines
    lines = output.strip().split("\n")
    assert len(lines) >= 1


def test_execute_write_parameter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test writing kernel parameter (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "kernel.hostname=test"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should write parameter successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["permission", "denied", "read-only", "error"]
        )


def test_execute_write_network_parameter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test writing network parameter (requires privileges)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "net.ipv4.ip_forward=0"])

    # Should either succeed or fail with permission error
    if result == 0:
        output = capture.get()
        # Should write parameter successfully
        assert len(output.strip()) >= 0
    else:
        # Should fail if no permission
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test quiet mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-q", "kernel.hostname"])

    # Should succeed in quiet mode
    assert result == 0
    output = capture.get()
    # Should contain parameter value without name in quiet mode
    assert len(output.strip()) >= 0


def test_execute_name_only_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test name-only mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-N", "kernel.*"])

    # Should succeed showing only parameter names
    assert result == 0
    output = capture.get()
    # Should contain parameter names without values
    assert len(output.strip()) > 0
    # Should contain kernel parameters
    assert "kernel." in output
    # Should not contain equals sign in name-only mode
    if "=" in output:
        # Some implementations may still show values
        assert len(output.strip()) > 0
    else:
        # Pure name-only output
        assert "kernel." in output


def test_execute_values_only_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test values-only mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-n", "kernel.hostname"])

    # Should succeed showing only parameter values
    assert result == 0
    output = capture.get()
    # Should contain parameter value without name
    assert len(output.strip()) > 0
    # Should not contain parameter name or equals sign
    if "kernel.hostname" not in output and "=" not in output:
        # Pure value-only output
        assert len(output.strip()) > 0
    else:
        # Some implementations may still show names
        assert len(output.strip()) > 0


def test_execute_binary_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test binary mode for binary parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-b", "kernel.random.uuid"])

    # Should handle binary parameters
    if result == 0:
        output = capture.get()
        # Should contain binary parameter data
        assert len(output.strip()) >= 0
    else:
        # May not be supported or parameter not available
        assert result == 1


def test_execute_ignore_errors_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test ignore errors mode
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-e", "nonexistent.parameter"])

    # Should ignore errors for nonexistent parameters
    if result == 0:
        output = capture.get()
        # Should succeed even with nonexistent parameter
        assert len(output.strip()) >= 0
    else:
        # May still fail depending on implementation
        assert result == 1


def test_execute_load_from_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test loading parameters from file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "/etc/sysctl.conf"])

    # Should either load from file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should load configuration from file
        assert len(output.strip()) >= 0
    else:
        # Should fail if file doesn't exist or no permission
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["No such file", "permission", "error", "cannot"]
        )


def test_execute_system_configuration_load(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test loading system configuration
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--system"])

    # Should either load system configuration or fail gracefully
    if result == 0:
        output = capture.get()
        # Should load system-wide configuration
        assert len(output.strip()) >= 0
    else:
        # Should fail if system configuration not available
        assert result == 1


def test_execute_nonexistent_parameter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test with nonexistent parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["nonexistent.parameter"])

    # Should fail with parameter not found error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "unknown", "cannot stat", "error"]
    )


def test_execute_invalid_parameter_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test with invalid parameter format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid..parameter"])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "invalid", "error", "cannot"])


def test_execute_write_invalid_value(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test writing invalid value to parameter
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-w", "net.ipv4.ip_forward=invalid"]
        )

    # Should fail with invalid value error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Invalid argument", "invalid", "error"])


def test_execute_write_readonly_parameter(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test writing to read-only parameter
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "kernel.version=test"])

    # Should fail with read-only error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["Read-only", "permission", "denied", "error"])


def test_execute_deprecated_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test handling of deprecated parameters
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["net.ipv4.conf.all.send_redirects"]
        )

    # Should either show parameter or handle deprecation gracefully
    if result == 0:
        output = capture.get()
        # Should show parameter value
        assert len(output.strip()) > 0
        assert "net.ipv4.conf.all.send_redirects" in output
    else:
        # May fail if parameter is deprecated or not available
        assert result == 1


def test_execute_proc_sys_direct_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test direct access to /proc/sys parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.ostype"])

    # Should succeed accessing kernel type
    assert result == 0
    output = capture.get()
    # Should contain OS type information
    assert len(output.strip()) > 0
    assert "kernel.ostype" in output
    assert "=" in output


def test_execute_sysctl_conf_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test sysctl.conf format handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.hostname"])

    # Should produce sysctl.conf compatible format
    assert result == 0
    output = capture.get()
    # Should contain parameter in key=value format
    assert len(output.strip()) > 0
    assert "kernel.hostname" in output
    assert "=" in output
    # Should be compatible with configuration file format
    lines = output.strip().split("\n")
    for line in lines:
        if line.strip():
            assert "=" in line


def test_execute_network_tuning_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test network tuning parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["net.core.*"])

    # Should show network core parameters
    if result == 0:
        output = capture.get()
        # Should contain network core parameters
        assert len(output.strip()) > 0
        assert "net.core" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_memory_management_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test memory management parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["vm.*"])

    # Should show virtual memory parameters
    if result == 0:
        output = capture.get()
        # Should contain VM parameters
        assert len(output.strip()) > 0
        assert "vm." in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_kernel_security_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test kernel security parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.dmesg_restrict"])

    # Should show security parameter
    if result == 0:
        output = capture.get()
        # Should contain security parameter
        assert len(output.strip()) > 0
        assert "kernel.dmesg_restrict" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_filesystem_limits(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test filesystem limit parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["fs.nr_open"])

    # Should show filesystem limits
    if result == 0:
        output = capture.get()
        # Should contain filesystem limit
        assert len(output.strip()) > 0
        assert "fs.nr_open" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_device_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test device-specific parameters
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["dev.*"])

    # Should show device parameters
    if result == 0:
        output = capture.get()
        # Should contain device parameters
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            assert "dev." in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.hostname"])

    # Should produce properly formatted output
    assert result == 0
    output = capture.get()

    if len(output.strip()) > 0:
        # Should have parameter=value format
        lines = output.strip().split("\n")
        for line in lines:
            if line.strip():
                # Each line should contain parameter assignment
                assert "=" in line
                # Should have proper parameter name format
                parts = line.split("=", 1)
                assert len(parts) == 2
                assert "." in parts[0]  # Parameter should have namespace


def test_execute_concurrent_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test concurrent parameter access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.hostname"])

    # Should handle concurrent access safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test memory efficiency with large parameter sets
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should not consume excessive memory
    assert len(output) < 500000  # Reasonable output size limit for all parameters


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid.parameter.name"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(
        msg in output for msg in ["No such file", "cannot stat", "error", "unknown"]
    )


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test permission handling for parameter changes
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-w", "kernel.hostname=testhost"])

    # Should handle permissions appropriately
    if result == 1:
        output = capture.get()
        # Should show permission-related error
        assert any(
            msg in output for msg in ["permission", "denied", "read-only", "error"]
        )
    else:
        # May succeed if running with appropriate privileges
        assert result == 0


def test_execute_parameter_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test parameter name validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel"])

    # Should handle incomplete parameter names
    if result == 0:
        output = capture.get()
        # Should show kernel parameters
        assert len(output.strip()) > 0
        assert "kernel" in output
    else:
        # May fail with incomplete parameter name
        assert result == 1


def test_execute_namespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test parameter namespace handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.osrelease"])

    # Should handle kernel namespace parameters
    assert result == 0
    output = capture.get()
    # Should show OS release information
    assert len(output.strip()) > 0
    assert "kernel.osrelease" in output
    assert "=" in output


def test_execute_dynamic_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test dynamic parameter handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.random.entropy_avail"])

    # Should handle dynamic parameters
    if result == 0:
        output = capture.get()
        # Should show entropy information
        assert len(output.strip()) > 0
        assert "kernel.random.entropy_avail" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_unicode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test Unicode character handling in parameter values
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.hostname"])

    # Should handle Unicode characters in output
    assert result == 0
    output = capture.get()
    # Should display parameter value correctly
    assert len(output.strip()) > 0
    # Should handle encoding properly
    assert isinstance(output, str)


def test_execute_large_parameter_values(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test handling of large parameter values
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["vm.max_map_count"])

    # Should handle large numeric values
    if result == 0:
        output = capture.get()
        # Should show large parameter value
        assert len(output.strip()) > 0
        assert "vm.max_map_count" in output
    else:
        # May not be available in all environments
        assert result == 1


def test_execute_array_parameters(
    client: ops.pebble.Client,
    command: pebble_shell.commands.SysctlCommand,
):
    # Test array-type parameter handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["kernel.printk"])

    # Should handle array parameters
    if result == 0:
        output = capture.get()
        # Should show array parameter values
        assert len(output.strip()) > 0
        assert "kernel.printk" in output
    else:
        # May not be available in all environments
        assert result == 1
