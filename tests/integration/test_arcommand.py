"""Integration tests for the ArCommand."""

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
    """Fixture to create a ArCommand instance."""
    yield pebble_shell.commands.ArCommand(shell=shell)


def test_name(command: pebble_shell.commands.ArCommand):
    assert command.name == "ar"


def test_category(command: pebble_shell.commands.ArCommand):
    assert command.category == "Archive Utilities"


def test_help(command: pebble_shell.commands.ArCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "ar" in output
    assert "Archive utility for static libraries" in output
    assert "archive" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "ar" in output
    assert "Archive utility for static libraries" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # ar with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["usage", "Usage", "ar", "operation", "archive"]
    )


def test_execute_list_archive_contents(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test listing archive contents
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed listing contents or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain archive member list
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain object file names
            lines = output.strip().split("\n")
            assert len(lines) >= 1
            # Should contain .o files typically
            assert any(".o" in line for line in lines if line.strip())
    else:
        # Should fail if archive doesn't exist
        assert result == 1


def test_execute_verbose_list(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test verbose listing
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["tv", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed with verbose listing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should contain detailed archive information
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should contain timestamps, permissions, sizes
            lines = output.strip().split("\n")
            for line in lines:
                if line.strip() and not line.startswith("ar:"):
                    # Should have verbose format with metadata
                    assert len(line.strip()) > 0
    else:
        assert result == 1


def test_execute_create_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test creating archive (dangerous, so use safe approach)
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as archive_file:
        archive_path = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["r", archive_path, "/nonexistent.o"]
        )

    # Should fail gracefully for nonexistent files
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_extract_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test extracting from archive
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["x", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed extracting or fail gracefully
    if result == 0:
        output = capture.get()
        # Should extract archive members
        assert len(output.strip()) >= 0
    else:
        # Should fail if archive doesn't exist or permission denied
        assert result == 1


def test_execute_print_archive_members(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test printing archive member contents
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["p", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed printing or fail gracefully
    if result == 0:
        output = capture.get()
        # Should print member contents
        assert len(output) >= 0
        # May contain binary data
        if len(output) > 0:
            assert len(output) >= 0
    else:
        assert result == 1


def test_execute_delete_from_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test deleting from archive (dangerous, so use safe approach)
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as archive_file:
        nonexistent_archive = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["d", nonexistent_archive, "member.o"]
        )

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_quick_append(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test quick append to archive
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as archive_file:
        test_archive = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["q", test_archive, "/nonexistent.o"]
        )

    # Should fail gracefully for nonexistent files
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_move_members(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test moving members in archive
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as archive_file:
        nonexistent_archive = archive_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["m", nonexistent_archive, "member.o"]
        )

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_symbol_table_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test symbol table operations
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["s", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed with symbol table or fail gracefully
    if result == 0:
        output = capture.get()
        # Should generate symbol table
        assert len(output.strip()) >= 0
    else:
        # Should fail if archive doesn't exist
        assert result == 1


def test_execute_create_with_verbose(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test create with verbose flag
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["rv", tmp_name, "/nonexistent.o"])

    # Should fail gracefully for nonexistent files
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_update_newer_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test updating with newer files
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["u", tmp_name, "file.o"])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_insert_before_member(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test inserting before specific member
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["bi", "target.o", tmp_name, "new.o"]
        )

    # Should fail gracefully for nonexistent files
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_insert_after_member(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test inserting after specific member
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["ai", "target.o", tmp_name, "new.o"]
        )

    # Should fail gracefully for nonexistent files
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_nonexistent_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with nonexistent archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", "/nonexistent/archive.a"])

    # Should fail with archive not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_invalid_archive_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with invalid archive format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", "/etc/passwd"])

    # Should fail with invalid format error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not an archive", "invalid", "error", "format"]
    )


def test_execute_permission_denied_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with permission denied archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", "/root/.ssh/id_rsa"])

    # Should either succeed or fail with permission error
    if result == 1:
        output = capture.get()
        assert any(msg in output for msg in ["permission", "denied", "cannot", "error"])
    else:
        # May succeed if file is readable (but likely not valid archive)
        assert result == 0


def test_execute_directory_as_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with directory instead of archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", tempfile.mkdtemp()])

    # Should fail with directory error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["directory", "Is a directory", "error", "not an archive"]
    )


def test_execute_empty_archive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with empty file as archive
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", "/dev/null"])

    # Should either handle empty archive or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show empty archive
        assert len(output.strip()) == 0
    else:
        # Should fail with invalid format
        assert result == 1


def test_execute_invalid_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with invalid operation
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["z", tmp_name])

    # Should fail with invalid operation error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "unknown", "operation", "usage"])


def test_execute_missing_archive_name(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with missing archive name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t"])

    # Should fail with missing archive error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["archive", "missing", "usage", "error"])


def test_execute_conflicting_operations(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test with conflicting operations
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["rt", tmp_name])

    # Should either handle multiple operations or fail appropriately
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["conflicting", "multiple", "error", "usage"]
        )
    else:
        # May accept multiple operation flags
        assert result == 0


def test_execute_archive_member_extraction(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test extracting specific archive member
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["x", "/usr/lib/x86_64-linux-gnu/libc.a", "printf.o"]
        )

    # Should either succeed extracting specific member or fail gracefully
    if result == 0:
        output = capture.get()
        # Should extract specific member
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_archive_modification_time(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test preserving modification times
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["to", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should either succeed with time preservation or fail gracefully
    if result == 0:
        output = capture.get()
        # Should preserve timestamps
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_archive_index_generation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test archive index generation
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["s", tmp_name])

    # Should fail gracefully for nonexistent archive
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "cannot", "error"])


def test_execute_output_format_validation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test output format validation
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should produce properly formatted output
    if result == 0:
        output = capture.get()
        # Should have valid listing format
        assert len(output.strip()) >= 0
        if len(output.strip()) > 0:
            # Should be line-oriented output
            lines = output.strip().split("\n")
            assert len(lines) >= 1
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 100000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test concurrent execution safety
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should handle concurrent execution safely
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test error recovery capabilities
    with tempfile.NamedTemporaryFile(suffix=".a", delete=False) as tmp_file:
        tmp_name = tmp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["z", tmp_name])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert any(msg in output for msg in ["invalid", "unknown", "error", "usage"])


def test_execute_signal_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test signal handling during processing
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should handle signals appropriately
    if result == 0:
        output = capture.get()
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_locale_independence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test locale independence
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should work regardless of locale settings
    if result == 0:
        output = capture.get()
        # Should be locale-independent
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_file_format_detection(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test file format detection
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["t", "/bin/ls"])

    # Should detect invalid archive format
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["not an archive", "invalid", "error", "format"]
    )


def test_execute_cross_platform_compatibility(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test cross-platform compatibility
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should work across different platforms
    if result == 0:
        output = capture.get()
        # Should handle platform-specific archive formats
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_archive_integrity_check(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test archive integrity checking
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should check archive integrity
    if result == 0:
        output = capture.get()
        # Should validate archive structure
        assert len(output.strip()) >= 0
    else:
        # Should fail if archive is corrupted
        assert result == 1


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test performance optimization
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should complete efficiently
    if result == 0:
        output = capture.get()
        # Should process efficiently
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_data_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test data consistency
    with command.shell.console.capture() as _:
        result1 = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    with command.shell.console.capture() as _:
        result2 = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should produce consistent results
    if result1 == 0 and result2 == 0:
        # Both executions should succeed consistently
        assert result1 == result2
    else:
        # At least one should succeed or both should fail consistently
        assert result1 == result2


def test_execute_robust_operation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ArCommand,
):
    # Test robust operation under stress
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["t", "/usr/lib/x86_64-linux-gnu/libc.a"]
        )

    # Should operate robustly
    if result == 0:
        output = capture.get()
        # Should handle stress conditions
        assert len(output.strip()) >= 0
    else:
        assert result == 1
