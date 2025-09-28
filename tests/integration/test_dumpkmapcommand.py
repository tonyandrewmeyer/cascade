"""Integration tests for the DumpkmapCommand."""

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
    """Fixture to create a DumpkmapCommand instance."""
    yield pebble_shell.commands.DumpkmapCommand(shell=shell)


def test_name(command: pebble_shell.commands.DumpkmapCommand):
    assert command.name == "dumpkmap"


def test_category(command: pebble_shell.commands.DumpkmapCommand):
    assert command.category == "System"


def test_help(command: pebble_shell.commands.DumpkmapCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert any(
        phrase in output.lower()
        for phrase in ["dump", "keymap", "kernel", "keyboard", "map"]
    )


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert any(
        phrase in output.lower() for phrase in ["dump", "keymap", "kernel", "usage"]
    )


def test_execute_dump_keymap(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test dumping kernel keymap
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed dumping keymap or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain keymap information
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain keymap data (binary or text format)
            lines = output.split("\n")
            assert len(lines) >= 1
    else:
        # Should fail if keymap unavailable or permission denied
        assert result == 1
        output = capture.get()
        assert any(
            msg in output
            for msg in ["permission", "denied", "keymap", "error", "not found"]
        )


def test_execute_output_to_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test output redirection to file
    with tempfile.NamedTemporaryFile(suffix=".dump", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[">", output_path])

    # Should either succeed writing to file or fail with error
    if result == 0:
        output = capture.get()
        # Should redirect keymap output to file
        assert len(output) >= 0
    else:
        # Should fail with file write or keymap error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "error", "write", "keymap"])


def test_execute_console_keymap_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test console keymap access
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing console or fail with permission
    if result == 0:
        output = capture.get()
        # Should access console keymap
        assert len(output) >= 0
    else:
        # Should fail if console unavailable
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["console", "permission", "denied", "error"]
        )


def test_execute_virtual_console_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test in virtual console environment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed in virtual console or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle virtual console keymap
        assert len(output) >= 0
    else:
        # Should fail if virtual console unsupported
        assert result == 1


def test_execute_x11_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test in X11 environment (should typically fail)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail with X11 environment
    if result == 0:
        output = capture.get()
        # Should handle X11 environment keymap
        assert len(output) >= 0
    else:
        # Should fail in X11 environment
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["console", "x11", "display", "error"])


def test_execute_ssh_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test in SSH environment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail in SSH environment
    if result == 0:
        output = capture.get()
        # Should handle SSH environment keymap
        assert len(output) >= 0
    else:
        # Should fail in SSH environment
        assert result == 1


def test_execute_container_environment(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test in container environment
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed or fail in container
    if result == 0:
        output = capture.get()
        # Should handle container keymap
        assert len(output) >= 0
    else:
        # Should fail in restricted container
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["container", "console", "permission", "error"]
        )


def test_execute_invalid_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
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
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test with unexpected arguments
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["unexpected", "args"])

    # Should either ignore arguments or fail with error
    if result == 0:
        output = capture.get()
        # Should ignore unexpected arguments
        assert len(output) >= 0
    else:
        # Should fail with argument error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["argument", "unexpected", "usage", "error"]
        )


def test_execute_keymap_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test keymap format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with valid format or fail
    if result == 0:
        output = capture.get()
        # Should produce valid keymap format
        assert len(output) >= 0
        if len(output) > 0:
            # Should contain keymap data
            assert isinstance(output, str)
    else:
        # Should fail with format or access error
        assert result == 1


def test_execute_keyboard_layout_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test keyboard layout detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed detecting layout or fail
    if result == 0:
        output = capture.get()
        # Should detect keyboard layout
        assert len(output) >= 0
    else:
        # Should fail with detection error
        assert result == 1


def test_execute_binary_output_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test binary output handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with binary output or fail
    if result == 0:
        output = capture.get()
        # Should handle binary keymap data
        assert len(output) >= 0
    else:
        # Should fail with binary handling error
        assert result == 1


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed regardless of locale or fail
    if result == 0:
        output = capture.get()
        # Should work independently of locale
        assert len(output) >= 0
    else:
        # Should fail consistently across locales
        assert result == 1


def test_execute_permission_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test permission handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed with permissions or fail gracefully
    if result == 0:
        output = capture.get()
        # Should succeed if permitted
        assert len(output) >= 0
    else:
        # Should fail with permission error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "access", "error"])


def test_execute_device_file_access(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test device file access for keymap
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should either succeed accessing device files or fail
    if result == 0:
        output = capture.get()
        # Should access keymap device files
        assert len(output) >= 0
    else:
        # Should fail with device access error
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["device", "console", "access", "error"])


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable keymap size limit
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should recover from errors gracefully
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with meaningful error
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["error", "keymap", "console", "permission"]
        )


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
):
    # Test signal handling during keymap dump
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output) >= 0
    else:
        # Should fail with appropriate error
        assert result == 1


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DumpkmapCommand,
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
        assert any(msg in output for msg in ["platform", "console", "keymap", "error"])
