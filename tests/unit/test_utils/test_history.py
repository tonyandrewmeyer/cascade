"""Tests for shell history functionality."""

import contextlib
import os
import tempfile
from unittest.mock import mock_open, patch

import pytest

from pebble_shell.utils.history import (
    ShellHistory,
    get_shell_history,
    init_shell_history,
)


class TestShellHistory:
    """Test cases for ShellHistory class."""

    @pytest.fixture
    def temp_history_file(self):
        """Create temporary history file."""
        fd, path = tempfile.mkstemp()
        os.close(fd)
        yield path
        with contextlib.suppress(FileNotFoundError):
            os.unlink(path)

    @pytest.fixture
    def history(self, temp_history_file):
        """Create ShellHistory instance with temp file."""
        return ShellHistory(max_size=10, history_file=temp_history_file)

    def test_init_empty_history(self, temp_history_file):
        """Test initialization with empty history."""
        history = ShellHistory(max_size=5, history_file=temp_history_file)
        assert history.max_size == 5
        assert history.history == []
        assert history.current_index == 0
        assert history.history_file == temp_history_file

    def test_add_command(self, history):
        """Test adding commands to history."""
        history.add_command("ls")
        history.add_command("pwd")

        assert len(history.history) == 2
        assert history.history == ["ls", "pwd"]
        assert history.current_index == 2

    def test_add_duplicate_consecutive(self, history):
        """Test that duplicate consecutive commands are not added."""
        history.add_command("ls")
        history.add_command("ls")
        history.add_command("pwd")
        history.add_command("pwd")

        assert len(history.history) == 2
        assert history.history == ["ls", "pwd"]

    def test_add_empty_command(self, history):
        """Test that empty commands are not added."""
        history.add_command("")
        history.add_command("   ")
        history.add_command("ls")

        assert len(history.history) == 1
        assert history.history == ["ls"]

    def test_add_history_command_filtered(self, history):
        """Test that history commands are filtered out."""
        history.add_command("ls")
        history.add_command("history")
        history.add_command("history -c")
        history.add_command("pwd")

        assert len(history.history) == 2
        assert history.history == ["ls", "pwd"]

    def test_max_size_limit(self, history):
        """Test that history respects max size limit."""
        # Add more commands than max_size (10)
        for i in range(15):
            history.add_command(f"command{i}")

        assert len(history.history) == 10
        assert history.history[0] == "command5"  # First 5 should be trimmed
        assert history.history[-1] == "command14"

    def test_get_previous(self, history):
        """Test getting previous commands."""
        history.add_command("ls")
        history.add_command("pwd")
        history.add_command("cat file.txt")

        # Start from end, go backwards
        assert history.get_previous() == "cat file.txt"
        assert history.get_previous() == "pwd"
        assert history.get_previous() == "ls"
        assert history.get_previous() is None  # At beginning

    def test_get_next(self, history):
        """Test getting next commands."""
        history.add_command("ls")
        history.add_command("pwd")
        history.add_command("cat file.txt")

        # Go to beginning first
        history.current_index = 0

        assert history.get_next() == "pwd"
        assert history.get_next() == "cat file.txt"
        assert history.get_next() is None  # At end

    def test_get_history_all(self, history):
        """Test getting all history."""
        commands = ["ls", "pwd", "cat file.txt"]
        for cmd in commands:
            history.add_command(cmd)

        assert history.get_history() == commands

    def test_get_history_count(self, history):
        """Test getting limited history."""
        commands = ["ls", "pwd", "cat file.txt", "echo hello"]
        for cmd in commands:
            history.add_command(cmd)

        assert history.get_history(2) == ["cat file.txt", "echo hello"]
        assert history.get_history(0) == []
        assert history.get_history(10) == commands  # More than available

    def test_search_history(self, history):
        """Test searching history."""
        commands = ["ls -la", "pwd", "cat file.txt", "ls /tmp", "echo hello"]
        for cmd in commands:
            history.add_command(cmd)

        results = history.search_history("ls")
        assert len(results) == 2
        assert "ls -la" in results
        assert "ls /tmp" in results

        results = history.search_history("cat")
        assert len(results) == 1
        assert "cat file.txt" in results

        results = history.search_history("nonexistent")
        assert len(results) == 0

    def test_clear_history(self, history):
        """Test clearing history."""
        history.add_command("ls")
        history.add_command("pwd")

        assert len(history.history) == 2

        history.clear_history()

        assert len(history.history) == 0
        assert history.current_index == 0

    def test_get_stats(self, history):
        """Test getting history statistics."""
        # Empty history
        stats = history.get_stats()
        assert stats["total_commands"] == 0
        assert stats["unique_commands"] == 0
        assert stats["most_used"] is None

        # Add some commands
        commands = ["ls", "pwd", "ls", "cat file.txt", "ls"]
        for cmd in commands:
            history.add_command(cmd)

        stats = history.get_stats()
        assert (
            stats["total_commands"] == 5
        )  # All commands kept (only consecutive duplicates removed)
        assert stats["unique_commands"] == 3
        assert stats["most_used"] == ("ls", 3)  # ls used 3 times

    @patch("builtins.open", new_callable=mock_open, read_data="ls\npwd\ncat file.txt\n")
    def test_load_history(self, _mock_file, temp_history_file):
        """Test loading history from file."""
        history = ShellHistory(history_file=temp_history_file)

        assert len(history.history) == 3
        assert history.history == ["ls", "pwd", "cat file.txt"]
        assert history.current_index == 3

    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_history(self, _mock_makedirs, mock_file, history):
        """Test saving history to file."""
        history.add_command("ls")
        history.add_command("pwd")

        # Verify file was written
        mock_file.assert_called()
        handle = mock_file()
        handle.write.assert_any_call("ls\n")
        handle.write.assert_any_call("pwd\n")

    def test_load_history_file_not_exists(self, temp_history_file):
        """Test loading when history file doesn't exist."""
        os.unlink(temp_history_file)  # Remove the file

        history = ShellHistory(history_file=temp_history_file)
        assert history.history == []
        assert history.current_index == 0

    @patch("builtins.open", side_effect=PermissionError)
    def test_save_history_permission_error(self, _mock_file, history):
        """Test save history with permission error."""
        # Should not raise exception
        history.add_command("ls")  # This triggers save

        # History should still be in memory
        assert len(history.history) == 1


class TestHistoryModule:
    """Test module-level history functions."""

    def test_get_shell_history_singleton(self):
        """Test that get_shell_history returns singleton."""
        history1 = get_shell_history()
        history2 = get_shell_history()

        assert history1 is history2

    def test_init_shell_history(self):
        """Test initializing shell history."""
        history = init_shell_history(max_size=5)

        assert isinstance(history, ShellHistory)
        assert history.max_size == 5

        # Should return same instance
        same_history = get_shell_history()
        assert history is same_history


class TestHistoryExpansion:
    """Test history expansion functionality."""

    @pytest.fixture
    def history_with_commands(self):
        """Create history with some commands for expansion testing."""
        # Use a temp file to avoid conflicts with other tests
        import tempfile

        fd, temp_file = tempfile.mkstemp()
        os.close(fd)

        history = ShellHistory(max_size=10, history_file=temp_file)
        # Clear any existing history from the file
        history.clear_history()

        history.add_command("ls -la")
        history.add_command("pwd")
        history.add_command("cat file.txt")
        history.add_command("echo 'hello world'")
        return history

    def test_expand_no_expansion_needed(self, history_with_commands):
        """Test commands that don't need expansion."""
        result = history_with_commands.expand_history("ls -l")
        assert result == "ls -l"

        result = history_with_commands.expand_history("")
        assert result == ""

        result = history_with_commands.expand_history("   ")
        assert result == "   "

    def test_quick_substitution_success(self, history_with_commands):
        """Test successful quick substitution."""
        result = history_with_commands.expand_history("^hello^goodbye")
        assert result == "echo 'goodbye world'"

    def test_quick_substitution_no_history(self):
        """Test quick substitution with no history."""
        # Use a fresh temp file to avoid shared state
        import tempfile

        fd, temp_file = tempfile.mkstemp()
        os.close(fd)

        history = ShellHistory(max_size=10, history_file=temp_file)
        history.clear_history()  # Ensure it's really empty

        from pebble_shell.utils.history import HistoryExpansionError

        with pytest.raises(HistoryExpansionError, match="No previous command"):
            history.expand_history("^old^new")

    def test_quick_substitution_with_single_caret(self, history_with_commands):
        """Test that commands with single ^ are not processed as substitution."""

        # Commands with only 1 ^ should not be processed as substitution
        result = history_with_commands.expand_history("^old")
        assert result == "^old"  # Should return unchanged

        result = history_with_commands.expand_history("^abc")
        assert result == "^abc"  # Should return unchanged

    def test_quick_substitution_text_not_found(self, history_with_commands):
        """Test quick substitution when text not found in last command."""
        from pebble_shell.utils.history import HistoryExpansionError

        with pytest.raises(
            HistoryExpansionError, match="'notfound' not found in last command"
        ):
            history_with_commands.expand_history("^notfound^replacement")

    def test_bang_expansion_last_command(self, history_with_commands):
        """Test !! expansion to last command."""
        result = history_with_commands.expand_history("!!")
        assert result == "echo 'hello world'"

    def test_bang_expansion_no_history(self):
        """Test !! expansion with no history."""
        # Use a fresh temp file to avoid shared state
        import tempfile

        fd, temp_file = tempfile.mkstemp()
        os.close(fd)

        history = ShellHistory(max_size=10, history_file=temp_file)
        history.clear_history()  # Ensure it's really empty

        from pebble_shell.utils.history import HistoryExpansionError

        with pytest.raises(HistoryExpansionError, match="No command history available"):
            history.expand_history("!!")

    def test_bang_expansion_by_number(self, history_with_commands):
        """Test !n expansion by command number."""
        result = history_with_commands.expand_history("!2")
        assert result == "pwd"

        result = history_with_commands.expand_history("!1")
        assert result == "ls -la"

    def test_bang_expansion_number_out_of_range(self, history_with_commands):
        """Test !n expansion with invalid number."""
        from pebble_shell.utils.history import HistoryExpansionError

        with pytest.raises(
            HistoryExpansionError, match="Command number 10 out of range"
        ):
            history_with_commands.expand_history("!10")

        with pytest.raises(
            HistoryExpansionError, match="Command number 0 out of range"
        ):
            history_with_commands.expand_history("!0")

    def test_bang_expansion_by_prefix(self, history_with_commands):
        """Test !prefix expansion by command prefix."""
        result = history_with_commands.expand_history("!cat")
        assert result == "cat file.txt"

        result = history_with_commands.expand_history("!ec")
        assert result == "echo 'hello world'"

    def test_bang_expansion_prefix_not_found(self, history_with_commands):
        """Test !prefix expansion when prefix not found."""
        from pebble_shell.utils.history import HistoryExpansionError

        with pytest.raises(
            HistoryExpansionError, match="No command found starting with 'xyz'"
        ):
            history_with_commands.expand_history("!xyz")

    def test_bang_expansion_non_bang_command(self, history_with_commands):
        """Test commands that don't start with ! or are too short."""
        result = history_with_commands.expand_history("ls")
        assert result == "ls"

        result = history_with_commands.expand_history("!")
        assert result == "!"

    def test_get_command_number(self, history_with_commands):
        """Test getting command number for a command."""
        assert history_with_commands.get_command_number("ls -la") == 1
        assert history_with_commands.get_command_number("pwd") == 2
        assert history_with_commands.get_command_number("cat file.txt") == 3
        assert history_with_commands.get_command_number("echo 'hello world'") == 4
        assert history_with_commands.get_command_number("nonexistent") is None

    def test_get_numbered_history_all(self, history_with_commands):
        """Test getting all numbered history."""
        result = history_with_commands.get_numbered_history()
        expected = [
            (1, "ls -la"),
            (2, "pwd"),
            (3, "cat file.txt"),
            (4, "echo 'hello world'"),
        ]
        assert result == expected

    def test_get_numbered_history_empty(self):
        """Test getting numbered history when empty."""
        # Use a fresh temp file to avoid shared state
        import tempfile

        fd, temp_file = tempfile.mkstemp()
        os.close(fd)

        history = ShellHistory(max_size=10, history_file=temp_file)
        history.clear_history()  # Ensure it's really empty

        result = history.get_numbered_history()
        assert result == []

    def test_get_numbered_history_with_start(self, history_with_commands):
        """Test getting numbered history with start parameter."""
        result = history_with_commands.get_numbered_history(start=2)
        expected = [(2, "pwd"), (3, "cat file.txt"), (4, "echo 'hello world'")]
        assert result == expected

        result = history_with_commands.get_numbered_history(start=3)
        expected = [(3, "cat file.txt"), (4, "echo 'hello world'")]
        assert result == expected

    def test_get_numbered_history_with_count(self, history_with_commands):
        """Test getting numbered history with count parameter."""
        result = history_with_commands.get_numbered_history(count=2)
        expected = [(1, "ls -la"), (2, "pwd")]
        assert result == expected

    def test_get_numbered_history_with_start_and_count(self, history_with_commands):
        """Test getting numbered history with both start and count."""
        result = history_with_commands.get_numbered_history(start=2, count=2)
        expected = [(2, "pwd"), (3, "cat file.txt")]
        assert result == expected

    def test_get_numbered_history_start_beyond_range(self, history_with_commands):
        """Test getting numbered history with start beyond range."""
        result = history_with_commands.get_numbered_history(start=10)
        assert result == []


class TestHistoryErrorHandling:
    """Test error handling in history functionality."""

    @patch("builtins.open", side_effect=Exception("File read error"))
    @patch("os.path.exists", return_value=True)
    def test_load_history_exception(self, mock_exists, mock_file):
        """Test _load_history exception handling."""
        # This should not raise an exception, but initialize empty history
        history = ShellHistory(max_size=10, history_file="/fake/path")
        assert history.history == []
        assert history.current_index == 0

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ls\npwd\n\n  \ncat file.txt\n",
    )
    @patch("os.path.exists", return_value=True)
    def test_load_history_with_empty_lines(self, mock_exists, mock_file):
        """Test loading history that contains empty and whitespace-only lines."""
        history = ShellHistory(max_size=10, history_file="/fake/path")
        # Empty lines and whitespace-only lines should be filtered out
        assert history.history == ["ls", "pwd", "cat file.txt"]
        assert history.current_index == 3

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="command1\ncommand2\ncommand3\ncommand4\ncommand5\ncommand6\n",
    )
    @patch("os.path.exists", return_value=True)
    def test_load_history_exceeds_max_size(self, mock_exists, mock_file):
        """Test loading history that exceeds max_size."""
        history = ShellHistory(max_size=3, history_file="/fake/path")
        # Should keep only the last 3 commands
        assert history.history == ["command4", "command5", "command6"]
        assert history.current_index == 3
