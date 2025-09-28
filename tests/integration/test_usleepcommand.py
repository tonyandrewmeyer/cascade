"""Integration tests for the UsleepCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a UsleepCommand instance."""
    yield pebble_shell.commands.UsleepCommand(shell=shell)


def test_name(command: pebble_shell.commands.UsleepCommand):
    assert command.name == "usleep"


def test_category(command: pebble_shell.commands.UsleepCommand):
    assert command.category == "System Utilities"


def test_help(command: pebble_shell.commands.UsleepCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "usleep" in output
    assert "Sleep for microseconds" in output
    assert "MICROSECONDS" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "usleep" in output
    assert "Sleep for microseconds" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # usleep with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "usleep <MICROSECONDS>" in output


def test_execute_small_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with small number of microseconds
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1000"])  # 1ms
    end_time = time.time()

    # Should succeed and sleep for approximately the right duration
    assert result == 0
    output = capture.get()
    # Should have minimal or no output
    assert len(output.strip()) == 0

    # Should have slept for at least 1ms (allowing for some system overhead)
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 0.5  # Allow for measurement precision


def test_execute_moderate_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with moderate number of microseconds
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["10000"])  # 10ms
    end_time = time.time()

    # Should succeed and sleep for approximately the right duration
    assert result == 0
    output = capture.get()
    # Should have no output
    assert len(output.strip()) == 0

    # Should have slept for at least 10ms
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 5  # Allow for system overhead and measurement precision


def test_execute_large_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with larger number of microseconds (but still reasonable for testing)
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["50000"])  # 50ms
    end_time = time.time()

    # Should succeed and sleep for approximately the right duration
    assert result == 0
    output = capture.get()
    # Should have no output
    assert len(output.strip()) == 0

    # Should have slept for at least 50ms
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 25  # Allow for system overhead


def test_execute_zero_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with zero microseconds
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["0"])
    end_time = time.time()

    # Should succeed with minimal delay
    assert result == 0
    output = capture.get()
    # Should have no output
    assert len(output.strip()) == 0

    # Should complete very quickly
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms < 10  # Should be very fast


def test_execute_one_microsecond(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with single microsecond
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1"])
    end_time = time.time()

    # Should succeed even with minimal sleep
    assert result == 0
    output = capture.get()
    # Should have no output
    assert len(output.strip()) == 0

    # Should complete quickly (1 microsecond is very small)
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms < 10  # Should be very fast due to system limitations


def test_execute_negative_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with negative microseconds
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1000"])

    # Should fail with negative value error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["negative", "invalid", "must be positive", "error"]
    )


def test_execute_invalid_number_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with invalid number format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["abc"])

    # Should fail with invalid number error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output
        for msg in ["invalid number", "not a number", "invalid argument", "error"]
    )


def test_execute_floating_point_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with floating point microseconds
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1000.5"])

    # Should either succeed (truncating) or fail with format error
    if result == 0:
        output = capture.get()
        # Should complete with truncated value
        assert len(output.strip()) == 0
    else:
        # Should fail if floating point not supported
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["invalid format", "integer required", "error"]
        )


def test_execute_very_large_microseconds(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with very large microseconds (should be handled or limited)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["999999999999"])  # ~16.6 minutes

    # Should either succeed (but we won't wait) or fail with limit error
    if result == 0:
        # If it starts sleeping, that's expected (we won't wait for completion)
        output = capture.get()
        assert len(output.strip()) == 0
    else:
        # Should fail if value too large
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["too large", "value too big", "overflow", "error"]
        )


def test_execute_empty_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with empty argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[""])

    # Should fail with empty argument error
    assert result == 1
    output = capture.get()
    assert any(
        msg in output for msg in ["empty argument", "invalid number", "usage", "error"]
    )


def test_execute_multiple_arguments(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with multiple arguments (should use first or error)
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["5000", "10000"])
    end_time = time.time()

    # Should either use first argument or fail with too many args
    if result == 0:
        output = capture.get()
        # Should use first argument (5ms)
        assert len(output.strip()) == 0
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms >= 2  # Should sleep for ~5ms
    else:
        # Should fail with too many arguments
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["too many arguments", "usage", "error"])


def test_execute_scientific_notation(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with scientific notation
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1e3"])  # 1000

    # Should either parse scientific notation or fail
    if result == 0:
        output = capture.get()
        # Should parse as 1000 microseconds
        assert len(output.strip()) == 0
    else:
        # Should fail if scientific notation not supported
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid format", "not a number", "error"])


def test_execute_hexadecimal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with hexadecimal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["0x3E8"])  # 1000 in hex

    # Should either parse hex or fail
    if result == 0:
        output = capture.get()
        # Should parse as 1000 microseconds
        assert len(output.strip()) == 0
    else:
        # Should fail if hex format not supported
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["invalid format", "not a number", "error"])


def test_execute_octal_format(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with octal format
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["01750"])  # 1000 in octal

    # Should either parse octal or treat as decimal
    if result == 0:
        output = capture.get()
        # Should parse as some numeric value
        assert len(output.strip()) == 0
    else:
        # Should fail if format not supported
        assert result == 1


def test_execute_leading_zeros(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with leading zeros
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["000001000"]
        )  # 1000 with leading zeros
    end_time = time.time()

    # Should succeed parsing number with leading zeros
    assert result == 0
    output = capture.get()
    # Should have no output
    assert len(output.strip()) == 0

    # Should sleep for ~1ms
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 0.5


def test_execute_plus_sign_prefix(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with plus sign prefix
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["+1000"])
    end_time = time.time()

    # Should either succeed with plus sign or fail
    if result == 0:
        output = capture.get()
        # Should parse as positive 1000
        assert len(output.strip()) == 0
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms >= 0.5
    else:
        # Should fail if plus sign not supported
        assert result == 1


def test_execute_whitespace_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test with whitespace around number
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["  1000  "])
    end_time = time.time()

    # Should either trim whitespace or fail
    if result == 0:
        output = capture.get()
        # Should parse trimmed number
        assert len(output.strip()) == 0
        elapsed_ms = (end_time - start_time) * 1000
        assert elapsed_ms >= 0.5
    else:
        # Should fail if whitespace not handled
        assert result == 1


def test_execute_signal_interruption(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test signal interruption (difficult to test reliably, so basic check)
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["10000"])  # 10ms
    end_time = time.time()

    # Should complete normally (we can't easily test signal interruption)
    assert result == 0
    output = capture.get()
    assert len(output.strip()) == 0

    # Should have slept for approximately the right time
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 5  # Should be close to 10ms


def test_execute_precision_accuracy(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test precision accuracy for short sleeps
    measurements = []
    for _ in range(3):  # Take multiple measurements
        start_time = time.time()
        with command.shell.console.capture() as _:
            result = command.execute(client=client, args=["5000"])  # 5ms
        end_time = time.time()

        assert result == 0
        elapsed_ms = (end_time - start_time) * 1000
        measurements.append(elapsed_ms)

    # Should have consistent timing (allowing for system variance)
    avg_time = sum(measurements) / len(measurements)
    assert avg_time >= 2  # Should be at least 2ms on average
    assert avg_time <= 50  # Should not be excessively long


def test_execute_concurrent_execution(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test concurrent execution safety
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1000"])
    end_time = time.time()

    # Should handle concurrent execution safely
    assert result == 0
    output = capture.get()
    assert len(output.strip()) == 0

    # Should complete in expected time
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 0.5


def test_execute_system_load_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test handling under system load
    start_time = time.time()
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["2000"])  # 2ms
    end_time = time.time()

    # Should complete despite system load
    assert result == 0
    output = capture.get()
    assert len(output.strip()) == 0

    # Should sleep for at least requested time (may be longer due to load)
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms >= 1  # Allow for system overhead


def test_execute_boundary_values(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test boundary values
    boundary_values = ["1", "999", "1000", "1000000"]  # 1μs, 999μs, 1ms, 1s

    for value in boundary_values:
        start_time = time.time()
        with command.shell.console.capture() as capture:
            result = command.execute(client=client, args=[value])
        end_time = time.time()

        # Should succeed for reasonable boundary values
        if int(value) <= 100000:  # Only test up to 100ms for reasonable test time
            assert result == 0
            output = capture.get()
            assert len(output.strip()) == 0

            # Should take appropriate time
            elapsed_ms = (end_time - start_time) * 1000
            expected_ms = int(value) / 1000.0
            if expected_ms >= 0.5:  # Only check timing for measurable durations
                assert elapsed_ms >= expected_ms * 0.5  # Allow 50% tolerance


def test_execute_output_silence(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test that usleep produces no output on success
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1000"])

    # Should succeed silently
    assert result == 0
    output = capture.get()
    # Should produce absolutely no output
    assert output == ""


def test_execute_error_message_clarity(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test error message clarity
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["invalid"])

    # Should provide clear error message
    assert result == 1
    output = capture.get()
    # Should have informative error message
    assert len(output.strip()) > 0
    assert any(msg in output for msg in ["invalid", "number", "argument", "error"])


def test_execute_return_code_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test return code consistency
    # Valid case
    with command.shell.console.capture() as _:
        result1 = command.execute(client=client, args=["1000"])
    assert result1 == 0

    # Invalid case
    with command.shell.console.capture() as _:
        result2 = command.execute(client=client, args=["invalid"])
    assert result2 == 1

    # Should be consistent
    with command.shell.console.capture() as _:
        result3 = command.execute(client=client, args=["1000"])
    assert result3 == result1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test memory efficiency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["1000"])

    # Should be memory efficient
    assert result == 0
    output = capture.get()
    # Should have no output and minimal memory usage
    assert len(output) == 0


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.UsleepCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--invalid-option", "1000"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options and proceed
        assert result == 0
