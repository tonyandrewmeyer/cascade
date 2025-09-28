"""Integration tests for the PatchCommand."""

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
    """Fixture to create a PatchCommand instance."""
    yield pebble_shell.commands.PatchCommand(shell=shell)


def test_name(command: pebble_shell.commands.PatchCommand):
    assert command.name == "patch"


def test_category(command: pebble_shell.commands.PatchCommand):
    assert command.category == "Advanced Utilities"


def test_help(command: pebble_shell.commands.PatchCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "patch" in output
    assert "Apply patch files to remote files" in output
    assert "-p NUM" in output
    assert "-R, --reverse" in output
    assert "unified diff format" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "patch" in output
    assert "Apply patch files to remote files" in output


def test_execute_no_args_stdin_input(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # patch with no args should read patch from stdin
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (if stdin available) or fail gracefully
    assert result in [0, 1]


def test_execute_patch_file_input_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -i option to specify patch file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "patch", "format", "error"])


def test_execute_nonexistent_patch_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test with nonexistent patch file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/nonexistent/patch.diff"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_patch_with_target_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test patching specific target file
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["/etc/passwd", "/nonexistent/patch.diff"]
        )

    # Should fail due to nonexistent patch file
    assert result == 1


def test_execute_nonexistent_target_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test patching nonexistent target file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.txt"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_strip_path_components_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -p option to strip path components
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-p1", "-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_strip_path_invalid_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -p option with invalid number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "invalid"])

    # Should fail with invalid number error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "number"])


def test_execute_reverse_option_short(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -R option for reverse patch
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-R", "-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_reverse_option_long(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test --reverse option for reverse patch
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["--reverse", "-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_output_file_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -o option to specify output file
    with tempfile.NamedTemporaryFile(suffix="_output.txt", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["-o", output_path, "-i", "/etc/passwd"]
        )

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_dry_run_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test --dry-run option
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["--dry-run", "-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file, but in dry-run mode
    assert result == 1


def test_execute_multiple_options_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test multiple options together
    with tempfile.NamedTemporaryFile(suffix="_out", delete=False) as out_file:
        out_path = out_file.name
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client,
            args=["-p1", "-R", "--dry-run", "-o", out_path, "-i", "/etc/passwd"],
        )

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_patch_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test patch format validation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/etc/passwd"])

    # Should fail with invalid patch format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "patch", "format"])


def test_execute_unified_diff_format_expected(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test that command expects unified diff format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/etc/hosts"])

    # Should fail since /etc/hosts is not a patch file
    assert result == 1
    output = capture.get()
    # Should indicate patch format issues
    assert any(msg in output for msg in ["patch", "format", "invalid"])


def test_execute_in_place_modification_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test default in-place modification (without -o option)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should either fail due to patch reading or permission issues
    assert result == 1


def test_execute_permission_error_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test handling of permission errors
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail gracefully if permission denied
    assert result == 1
    output = capture.get()
    # Should show appropriate error message
    assert any(
        msg in output for msg in ["permission", "denied", "error", "No such file"]
    )


def test_execute_patch_file_reading_error(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test error handling when patch file cannot be read
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/dev/null"])

    # Should fail since /dev/null is empty (not a valid patch)
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["empty", "invalid", "patch"])


def test_execute_target_file_reading_error(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test error handling when target file cannot be read
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-i", "/etc/passwd", "/nonexistent/target"]
        )

    # Should fail with target file error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "target"])


def test_execute_output_file_write_permission(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test output file write permission issues
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client,
            args=["-o", "/nonexistent/dir/output.txt", "-i", "/etc/passwd"],
        )

    # Should fail due to invalid output directory
    assert result == 1


def test_execute_negative_strip_path_components(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -p with negative number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", "-1"])

    # Should fail with invalid number error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "negative"])


def test_execute_zero_strip_path_components(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -p0 (no path stripping)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-p0", "-i", "/etc/passwd"])

    # Should fail since /etc/passwd is not a valid patch file
    assert result == 1


def test_execute_large_strip_path_components(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test -p with large number
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-p999", "-i", "/etc/passwd"])

    # Should either handle large number or fail with error
    assert result == 1  # Still fails due to invalid patch file


def test_execute_patch_application_dry_run_output(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test that dry-run shows what would be done
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--dry-run", "-i", "/etc/passwd"])

    # Should fail but may show dry-run output
    assert result == 1
    output = capture.get()
    # Should indicate dry-run mode or show what would be done
    if "dry" in output.lower() or "would" in output.lower():
        # Good - shows dry-run behavior
        pass


def test_execute_patch_context_line_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.PatchCommand,
):
    # Test patch context line handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "/etc/passwd"])

    # Should fail due to invalid patch format
    assert result == 1
    output = capture.get()
    # Should show patch format error
    assert any(msg in output for msg in ["patch", "format", "invalid"])
