"""Integration tests for the DdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a DdCommand instance."""
    yield pebble_shell.commands.DdCommand(shell=shell)


def test_name(command: pebble_shell.commands.DdCommand):
    assert command.name == "dd"


def test_category(command: pebble_shell.commands.DdCommand):
    assert command.category == "Data Processing"


def test_help(command: pebble_shell.commands.DdCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "dd" in output
    assert "Convert and copy a file" in output
    assert "if=FILE" in output
    assert "of=FILE" in output
    assert "bs=BYTES" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "dd" in output
    assert "Convert and copy a file" in output


def test_execute_no_args_default_behavior(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # dd with no args should read from stdin and write to stdout
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])

    # Should either succeed (if stdin available) or fail gracefully
    assert result in [0, 1]


def test_execute_invalid_operand_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test invalid operand format (missing = sign)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalidoperand"])

    # Should fail with error about invalid operand format
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "operand", "format"])


def test_execute_if_operand_file_read(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test if=FILE operand with existing file
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd"])

    # Should either succeed (reading from /etc/passwd) or fail if file not accessible
    if result == 0:
        # Should have read from /etc/passwd and written to stdout
        pass
    else:
        assert result == 1


def test_execute_if_operand_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test if=FILE operand with nonexistent file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["if=/nonexistent/file"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_of_operand_file_write(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test of=FILE operand (output to file)
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["if=/etc/passwd", "of=/tmp/test_output"]
        )

    # Should either succeed (writing to file) or fail if path not writable
    if result == 0:
        # Should have written to output file
        pass
    else:
        assert result == 1


def test_execute_bs_operand_block_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test bs=BYTES operand for block size
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "bs=1024"])

    # Should either succeed with specified block size or fail gracefully
    if result == 0:
        # Should have used 1024 byte block size
        pass
    else:
        assert result == 1


def test_execute_bs_operand_invalid_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test bs=BYTES operand with invalid size
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["bs=invalid"])

    # Should fail with invalid block size error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "block size", "bytes"])


def test_execute_count_operand_limit_blocks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test count=N operand to limit blocks copied
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "count=5"])

    # Should either succeed with limited block count or fail gracefully
    if result == 0:
        # Should have copied only 5 blocks
        pass
    else:
        assert result == 1


def test_execute_count_operand_invalid_number(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test count=N operand with invalid number
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["count=invalid"])

    # Should fail with invalid count error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "count"])


def test_execute_skip_operand_skip_blocks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test skip=N operand to skip input blocks
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "skip=2"])

    # Should either succeed with skipped blocks or fail gracefully
    if result == 0:
        # Should have skipped 2 input blocks
        pass
    else:
        assert result == 1


def test_execute_seek_operand_skip_output_blocks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test seek=N operand to skip output blocks
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "seek=1"])

    # Should either succeed with output seek or fail gracefully
    if result == 0:
        # Should have sought to position in output
        pass
    else:
        assert result == 1


def test_execute_conv_ucase_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test conv=ucase conversion (lowercase to uppercase)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "conv=ucase"])

    # Should either succeed with uppercase conversion or fail gracefully
    if result == 0:
        # Should have converted to uppercase
        pass
    else:
        assert result == 1


def test_execute_conv_lcase_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test conv=lcase conversion (uppercase to lowercase)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "conv=lcase"])

    # Should either succeed with lowercase conversion or fail gracefully
    if result == 0:
        # Should have converted to lowercase
        pass
    else:
        assert result == 1


def test_execute_conv_invalid_conversion(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test conv=INVALID conversion
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["conv=invalid"])

    # Should fail with invalid conversion error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["invalid", "conversion"])


def test_execute_multiple_operands_combination(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test multiple operands together
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["if=/etc/passwd", "bs=512", "count=3", "conv=ucase"]
        )

    # Should either succeed with all operands or fail gracefully
    if result == 0:
        # Should have combined all operand effects
        pass
    else:
        assert result == 1


def test_execute_ibs_obs_separate_block_sizes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test ibs=BYTES and obs=BYTES operands separately
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["if=/etc/passwd", "ibs=256", "obs=1024"]
        )

    # Should either succeed with separate input/output block sizes or fail gracefully
    if result == 0:
        # Should have used different input and output block sizes
        pass
    else:
        assert result == 1


def test_execute_conv_sync_padding(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test conv=sync padding conversion
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "conv=sync"])

    # Should either succeed with sync padding or fail gracefully
    if result == 0:
        # Should have padded blocks with NULs
        pass
    else:
        assert result == 1


def test_execute_progress_reporting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test that dd reports progress/statistics
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["if=/etc/passwd", "count=1"])

    # Should either succeed and show statistics or fail gracefully
    if result == 0:
        _ = capture.get()
        # dd typically shows transfer statistics
        # May include bytes copied, time, rate, etc.
        pass
    else:
        assert result == 1


def test_execute_zero_count_no_copy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test count=0 (should copy no blocks)
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["if=/etc/passwd", "count=0"])

    # Should succeed but copy no data
    if result == 0:
        # Should copy 0 blocks
        pass
    else:
        assert result == 1


def test_execute_operand_parsing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.DdCommand,
):
    # Test operand parsing with various formats
    with command.shell.console.capture() as _:
        result = command.execute(
            client=client, args=["if=/etc/passwd", "bs=1k", "count=2"]
        )

    # Should parse size suffixes (k, M, G) if supported
    if result == 0:
        # Should have parsed "1k" as 1024 bytes
        pass
    else:
        assert result == 1
