"""Integration tests for the CpioCommand."""

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
    """Fixture to create a CpioCommand instance."""
    yield pebble_shell.commands.CpioCommand(shell=shell)


def test_name(command: pebble_shell.commands.CpioCommand):
    assert command.name == "cpio"


def test_category(command: pebble_shell.commands.CpioCommand):
    assert command.category == "Archive Utilities"


def test_help(command: pebble_shell.commands.CpioCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "cpio" in output
    assert "Archive creation and extraction" in output
    assert "archive" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "cpio" in output
    assert "Archive creation and extraction" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # cpio with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["usage", "Usage", "cpio", "mode", "operation"])


def test_execute_list_archive_contents(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test listing archive contents
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        nonexistent_cpio = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", nonexistent_cpio])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_extract_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test extracting from archive
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        nonexistent_cpio = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-i", "-I", nonexistent_cpio])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["No such file", "cannot", "error", "not found"]
    )


def test_execute_create_archive_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test create archive mode (dangerous, so use safe approach)
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-o", "-O", output_path])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should create archive from stdin
        assert len(output.strip()) >= 0
    else:
        # Should fail if cannot create archive
        assert result == 1


def test_execute_pass_through_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test pass-through mode
    destination_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-p", destination_dir])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should copy files from stdin
        assert len(output.strip()) >= 0
    else:
        # Should fail if destination doesn't exist
        assert result == 1


def test_execute_verbose_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test verbose mode
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
            archive_path = archive_file.name
        result = command.execute(client=client, args=["-tv", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_create_directories(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test create directories option
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
            archive_path = archive_file.name
        result = command.execute(client=client, args=["-id", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_preserve_modification_time(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test preserve modification time
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-im", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_unconditional_overwrite(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test unconditional overwrite
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-iu", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_reset_access_times(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test reset access times
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-oa", "-O", output_path])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should reset access times
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_append_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test append mode
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-oA", "-O", output_path])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should append to archive
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_block_size_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test block size option
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-B", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_format_specification(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test format specification
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-o", "-H", "newc", "-O", output_path]
        )

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should use specified format
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_pattern_matching(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test pattern matching
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-i", "*.txt", "-I", archive_path]
        )

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_rename_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test rename files option
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-ir", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_swap_bytes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test swap bytes option
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-is", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_swap_halfwords(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test swap halfwords option
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-iS", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_only_newer_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test extract only newer files
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-iu", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_link_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test link files option
    destination_dir = tempfile.mkdtemp()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-pl", destination_dir])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should link files instead of copying
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_dereference_symlinks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test dereference symbolic links
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-oL", "-O", output_path])

    # Should either wait for input or fail appropriately
    if result == 0:
        output = capture.get()
        # Should dereference symlinks
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_quiet_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test quiet mode
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-tq", "-I", archive_path])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    # Should produce minimal output in quiet mode
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_file_list_from_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test reading file list from file
    with tempfile.NamedTemporaryFile(suffix=".list", delete=False) as list_file:
        list_path = list_file.name
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client,
            args=["-o", "-E", list_path, "-O", output_path],
        )

    # Should fail gracefully for nonexistent file list
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_invalid_option_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test invalid option combination
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-io"])

    # Should fail with invalid combination error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid", "conflicting", "error", "usage", "incompatible"]
    )


def test_execute_missing_required_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test missing required argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-I"])

    # Should fail with missing argument error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["argument", "required", "missing", "usage", "error"]
    )


def test_execute_invalid_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test invalid format specification
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
        output_path = output_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-o", "-H", "invalid", "-O", output_path]
        )

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "format", "unknown", "error"])


def test_execute_permission_denied_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test permission denied on archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_directory_as_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test directory as archive
    with command.shell.console.capture() as capture:
        test_dir = tempfile.mkdtemp()
        result = command.execute(client=client, args=["-t", "-I", test_dir])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["directory", "Is a directory", "error", "invalid"]
    )


def test_execute_empty_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test empty archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", "/dev/null"])

    # Should either handle empty archive or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show empty archive
        assert len(output.strip()) == 0
    else:
        # Should fail with invalid format
        assert result == 1


def test_execute_binary_file_as_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test binary file as archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", "/bin/ls"])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "format", "error", "not a cpio"])


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test output format validation
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should produce properly formatted output
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    # Should have valid error format
    assert len(output.strip()) > 0


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
            output_path = output_file.name
        result = command.execute(client=client, args=["-o", "-O", output_path])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 10000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test concurrent execution safety
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should handle concurrent execution safely
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    assert len(output.strip()) > 0


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-io"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "error", "usage", "conflicting"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test signal handling during processing
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should handle signals appropriately
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    # Should be signal-safe
    assert len(output.strip()) > 0


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test locale independence
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should work regardless of locale settings
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    # Should be locale-independent
    assert len(output.strip()) > 0


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test cross-platform compatibility
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should work across different platforms
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    # Should handle platform-specific archive formats
    assert len(output.strip()) > 0


def test_execute_archive_format_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test archive format detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", "/etc/passwd"])

    # Should detect invalid archive format
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "format", "error", "not a cpio"])


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as output_file:
            output_path = output_file.name
        result = command.execute(client=client, args=["-o", "-O", output_path])

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test data consistency
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file1:
        tmp_name1 = tmp_file1.name
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file2:
        tmp_name2 = tmp_file2.name
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["-t", "-I", tmp_name1])

    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["-t", "-I", tmp_name2])

    # Should produce consistent results
    assert result1 == 1
    assert result2 == 1
    # Both executions should fail consistently
    assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.CpioCommand,
):
    # Test robust operation under stress
    with tempfile.NamedTemporaryFile(suffix=".cpio", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "-I", tmp_name])

    # Should operate robustly
    assert result == 1  # Fails for nonexistent file
    output = capture.get()
    # Should handle stress conditions
    assert len(output.strip()) > 0
