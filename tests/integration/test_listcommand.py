"""Integration tests for the ListCommand."""

from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a ListCommand instance."""
    yield pebble_shell.commands.ListCommand(shell=shell)


TEST_DIR = "/tmp/cascade_ls_test"  # noqa: S108


@pytest.fixture(scope="session")
def ls_test_tree(client: ops.pebble.Client):
    """Create a test directory tree on Pebble for ls tests.

    Structure:
        /tmp/cascade_ls_test/
        ├── alpha.txt      (small file, oldest)
        ├── bravo.txt      (larger file, newest)
        ├── charlie.txt    (medium file, middle)
        ├── .hidden        (dot file)
        └── subdir/
            └── nested.txt
    """
    client.make_dir(f"{TEST_DIR}/subdir", make_parents=True)
    # Push files with small delays so modification times differ.
    client.push(f"{TEST_DIR}/alpha.txt", "a\n")
    time.sleep(1.1)
    client.push(f"{TEST_DIR}/charlie.txt", "ccc\nccc\nccc\n")
    time.sleep(1.1)
    client.push(f"{TEST_DIR}/bravo.txt", "bbbbb\nbbbbb\nbbbbb\nbbbbb\nbbbbb\n")
    client.push(f"{TEST_DIR}/.hidden", "secret\n")
    client.push(f"{TEST_DIR}/subdir/nested.txt", "nested\n")

    # Also create an empty directory for the empty-dir test.
    client.make_dir(f"{TEST_DIR}/emptydir", make_parents=True)

    yield TEST_DIR

    # Cleanup
    with contextlib.suppress(Exception):
        client.remove_path(TEST_DIR, recursive=True)


# ── Existing basic tests ────────────────────────────────────────────


def test_name(command: pebble_shell.commands.ListCommand):
    assert command.name == "ls"


def test_category(command: pebble_shell.commands.ListCommand):
    assert command.category == "Filesystem Commands"


def test_help(command: pebble_shell.commands.ListCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    assert "List directory contents" in capture.get()


@pytest.mark.parametrize("args", [["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    assert "List directory contents" in capture.get()


def test_execute_default(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=[])
    assert result == 0


def test_execute_root_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["/"])
    assert result == 0


def test_execute_nonexistent_directory(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])
    assert result == 1
    assert "cannot list directory" in capture.get()


# ── New POSIX-compliance tests ──────────────────────────────────────


def test_basic_listing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Lists known files, returns 0."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[ls_test_tree])
    assert result == 0
    output = capture.get()
    assert "alpha.txt" in output
    assert "bravo.txt" in output
    assert "charlie.txt" in output


def test_default_hides_dot_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """.hidden absent without -a."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[ls_test_tree])
    assert result == 0
    assert ".hidden" not in capture.get()


def test_flag_a_shows_dot_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """.hidden present with -a."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-a", ls_test_tree])
    assert result == 0
    assert ".hidden" in capture.get()


def test_flag_l_long_listing(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Output has mode, owner, group, size, time, name columns."""
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "--plain-timestamp", ls_test_tree]
        )
    assert result == 0
    output = capture.get()
    # Long listing should contain permission strings and file names
    assert "alpha.txt" in output
    # Permission string like -rw-r--r-- or drwxr-xr-x
    assert "rw" in output


def test_flag_h_human_readable_sizes(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Sizes show units (B, KB, etc.)."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-lh", ls_test_tree])
    assert result == 0
    output = capture.get()
    # Human-readable sizes should contain a unit
    assert "B" in output


def test_combined_la(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Long listing including dot files."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-la", ls_test_tree])
    assert result == 0
    output = capture.get()
    assert ".hidden" in output
    # Should also have permission columns
    assert "rw" in output


def test_combined_lh(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Long listing with human sizes."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-lh", ls_test_tree])
    assert result == 0
    output = capture.get()
    assert "alpha.txt" in output
    assert "B" in output


def test_default_alphabetical_sort(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Files appear in alphabetical order."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1", ls_test_tree])
    assert result == 0
    lines = [ln.strip() for ln in capture.get().splitlines() if ln.strip()]
    names = [ln for ln in lines if ln in ("alpha.txt", "bravo.txt", "charlie.txt", "subdir")]
    assert names == sorted(names)


def test_flag_t_sort_by_time(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Files sorted newest-first."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1t", ls_test_tree])
    assert result == 0
    lines = [ln.strip() for ln in capture.get().splitlines() if ln.strip()]
    # bravo.txt was pushed last, alpha.txt first
    file_lines = [ln for ln in lines if ln in ("alpha.txt", "bravo.txt", "charlie.txt")]
    assert file_lines.index("bravo.txt") < file_lines.index("alpha.txt")


def test_flag_sort_by_size(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Files sorted largest-first."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1S", ls_test_tree])
    assert result == 0
    lines = [ln.strip() for ln in capture.get().splitlines() if ln.strip()]
    file_lines = [ln for ln in lines if ln in ("alpha.txt", "bravo.txt", "charlie.txt")]
    # bravo.txt is largest, alpha.txt is smallest
    assert file_lines.index("bravo.txt") < file_lines.index("alpha.txt")


def test_flag_r_reverse_sort(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Reverses default alphabetical."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1r", ls_test_tree])
    assert result == 0
    lines = [ln.strip() for ln in capture.get().splitlines() if ln.strip()]
    names = [ln for ln in lines if ln in ("alpha.txt", "bravo.txt", "charlie.txt", "subdir")]
    assert names == sorted(names, reverse=True)


def test_flag_1_one_per_line(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Plain text output, one name per line."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-1", ls_test_tree])
    assert result == 0
    lines = [ln.strip() for ln in capture.get().splitlines() if ln.strip()]
    # Each line should be exactly a filename (no table chrome)
    expected_names = {"alpha.txt", "bravo.txt", "charlie.txt", "subdir"}
    assert expected_names == set(lines)


def test_flag_recursive(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Lists subdirectories with headers."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-R1", ls_test_tree])
    assert result == 0
    output = capture.get()
    # Should contain the subdir header
    assert "subdir" in output
    # Should contain the nested file
    assert "nested.txt" in output


def test_nonexistent_path_returns_1(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    """Exit code 1, error message."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/no/such/path"])
    assert result == 1
    assert "cannot list directory" in capture.get()


def test_empty_directory_returns_0(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Exit code 0, empty message."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[f"{ls_test_tree}/emptydir"])
    assert result == 0
    assert "empty" in capture.get().lower()


def test_plain_timestamp(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """--plain-timestamp shows YYYY-MM-DD format."""
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["-l", "--plain-timestamp", ls_test_tree]
        )
    assert result == 0
    output = capture.get()
    # Should contain a date in YYYY-MM-DD format
    import re

    assert re.search(r"\d{4}-\d{2}-\d{2}", output)


def test_help_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
):
    """--help shows help text."""
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--help"])
    assert result == 0
    assert "List directory contents" in capture.get()


def test_invalid_flag(
    client: ops.pebble.Client,
    command: pebble_shell.commands.ListCommand,
    ls_test_tree: str,
):
    """Unknown flag returns 1."""
    with command.shell.console.capture() as _:
        result = command.execute(client=client, args=["-Z", ls_test_tree])
    assert result == 1
