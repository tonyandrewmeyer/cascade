"""Tests for readline support utilities."""

from __future__ import annotations

from unittest.mock import Mock, patch

from pebble_shell.utils.readline_support import (
    ReadlineWrapper,
    ShellCompleter,
    setup_readline_support,
)


class TestReadlineWrapper:
    """Test ReadlineWrapper class."""

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_init_no_readline(self) -> None:
        """Test initialization when readline is not available."""
        wrapper = ReadlineWrapper()
        assert not wrapper.has_readline
        assert wrapper.completer_function is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_init_with_readline(self, mock_readline: Mock) -> None:
        """Test initialization when readline is available."""
        wrapper = ReadlineWrapper()
        assert wrapper.has_readline

        # Verify readline configuration calls
        mock_readline.parse_and_bind.assert_any_call("tab: complete")
        mock_readline.parse_and_bind.assert_any_call('"\\e[A": history-search-backward')
        mock_readline.parse_and_bind.assert_any_call('"\\e[B": history-search-forward')
        mock_readline.set_history_length.assert_called_once_with(1000)

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_set_completer_no_readline(self) -> None:
        """Test setting completer when readline is not available."""
        wrapper = ReadlineWrapper()
        completer = Mock()

        # Should not raise an error
        wrapper.set_completer(completer)
        assert wrapper.completer_function is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_set_completer_with_readline(self, mock_readline: Mock) -> None:
        """Test setting completer when readline is available."""
        wrapper = ReadlineWrapper()
        completer = Mock()

        wrapper.set_completer(completer)
        assert wrapper.completer_function is completer
        mock_readline.set_completer.assert_called_once_with(completer)

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_add_history_no_readline(self) -> None:
        """Test adding history when readline is not available."""
        wrapper = ReadlineWrapper()

        # Should not raise an error
        wrapper.add_history("test command")

    @patch("pebble_shell.utils.readline_support.readline")
    def test_add_history_with_readline(self, mock_readline: Mock) -> None:
        """Test adding history when readline is available."""
        wrapper = ReadlineWrapper()

        wrapper.add_history("test command")
        mock_readline.add_history.assert_called_once_with("test command")

    @patch("pebble_shell.utils.readline_support.readline")
    def test_add_history_empty_line(self, mock_readline: Mock) -> None:
        """Test adding empty history line."""
        wrapper = ReadlineWrapper()

        wrapper.add_history("")
        wrapper.add_history("   ")

        # Should not call add_history for empty/whitespace-only lines
        mock_readline.add_history.assert_not_called()

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_clear_history_no_readline(self) -> None:
        """Test clearing history when readline is not available."""
        wrapper = ReadlineWrapper()

        # Should not raise an error
        wrapper.clear_history()

    @patch("pebble_shell.utils.readline_support.readline")
    def test_clear_history_with_readline(self, mock_readline: Mock) -> None:
        """Test clearing history when readline is available."""
        wrapper = ReadlineWrapper()

        wrapper.clear_history()
        mock_readline.clear_history.assert_called_once()

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_get_history_length_no_readline(self) -> None:
        """Test getting history length when readline is not available."""
        wrapper = ReadlineWrapper()

        assert wrapper.get_history_length() == 0

    @patch("pebble_shell.utils.readline_support.readline")
    def test_get_history_length_with_readline(self, mock_readline: Mock) -> None:
        """Test getting history length when readline is available."""
        wrapper = ReadlineWrapper()
        mock_readline.get_current_history_length.return_value = 42

        assert wrapper.get_history_length() == 42
        mock_readline.get_current_history_length.assert_called_once()

    @patch("pebble_shell.utils.readline_support.readline", None)
    def test_get_history_item_no_readline(self) -> None:
        """Test getting history item when readline is not available."""
        wrapper = ReadlineWrapper()

        assert wrapper.get_history_item(0) is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_get_history_item_with_readline(self, mock_readline: Mock) -> None:
        """Test getting history item when readline is available."""
        wrapper = ReadlineWrapper()
        mock_readline.get_history_item.return_value = "test command"

        result = wrapper.get_history_item(0)
        assert result == "test command"
        mock_readline.get_history_item.assert_called_once_with(
            1
        )  # readline is 1-indexed

    @patch("pebble_shell.utils.readline_support.readline")
    def test_get_history_item_index_error(self, mock_readline: Mock) -> None:
        """Test getting history item with invalid index."""
        wrapper = ReadlineWrapper()
        mock_readline.get_history_item.side_effect = IndexError()

        result = wrapper.get_history_item(999)
        assert result is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_get_history_item_value_error(self, mock_readline: Mock) -> None:
        """Test getting history item with value error."""
        wrapper = ReadlineWrapper()
        mock_readline.get_history_item.side_effect = ValueError()

        result = wrapper.get_history_item(-1)
        assert result is None

    @patch("builtins.input", return_value="user input")
    def test_input_with_prompt(self, mock_input: Mock) -> None:
        """Test getting input with prompt."""
        wrapper = ReadlineWrapper()

        result = wrapper.input_with_prompt("test> ")
        assert result == "user input"
        mock_input.assert_called_once_with("test> ")


class TestShellCompleter:
    """Test ShellCompleter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.commands = {
            "cat": Mock(),
            "ls": Mock(),
            "pwd": Mock(),
        }
        self.alias_command = Mock()
        self.alias_command.aliases = {"ll": "ls -la", "la": "ls -a"}

        self.completer = ShellCompleter(self.commands, self.alias_command)

    def test_init(self) -> None:
        """Test completer initialization."""
        assert self.completer.commands is self.commands
        assert self.completer.alias_command is self.alias_command

        expected_commands = ["cat", "ls", "pwd", "help", "exit", "clear"]
        for cmd in expected_commands:
            assert cmd in self.completer.command_names

    @patch("pebble_shell.utils.readline_support.readline")
    def test_complete_command_names(self, mock_readline: Mock) -> None:
        """Test completing command names."""
        mock_readline.get_line_buffer.return_value = "c"

        # First call (state=0) should generate matches
        result = self.completer.complete("c", 0)
        assert result in ["cat", "clear"]

        # Second call (state=1) should return next match
        result = self.completer.complete("c", 1)
        assert result in ["cat", "clear"]

        # Third call (state=2) should return None (no more matches)
        result = self.completer.complete("c", 2)
        assert result is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_complete_aliases(self, mock_readline: Mock) -> None:
        """Test completing alias names."""
        mock_readline.get_line_buffer.return_value = "l"

        result = self.completer.complete("l", 0)
        assert result in ["ll", "la", "ls"]

    @patch("pebble_shell.utils.readline_support.readline")
    @patch("glob.glob")
    def test_complete_path(self, mock_glob: Mock, mock_readline: Mock) -> None:
        """Test completing file paths."""
        mock_readline.get_line_buffer.return_value = "cat test"
        mock_glob.return_value = ["/home/test.txt", "/home/testdir"]

        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.side_effect = lambda path: path.endswith("testdir")

            result = self.completer.complete("test", 0)
            assert result in ["/home/test.txt", "/home/testdir/"]

    @patch("pebble_shell.utils.readline_support.readline")
    @patch("glob.glob")
    def test_complete_path_empty_text(
        self, mock_glob: Mock, mock_readline: Mock
    ) -> None:
        """Test completing paths with empty text."""
        mock_readline.get_line_buffer.return_value = "cat "
        mock_glob.return_value = ["file1.txt", "file2.txt"]

        with patch("os.path.isdir", return_value=False):
            self.completer.complete("", 0)
            mock_glob.assert_called_with("./*")

    @patch("pebble_shell.utils.readline_support.readline")
    @patch("glob.glob")
    def test_complete_path_with_slash(
        self, mock_glob: Mock, mock_readline: Mock
    ) -> None:
        """Test completing paths ending with slash."""
        mock_readline.get_line_buffer.return_value = "cat /home/"
        mock_glob.return_value = ["/home/file.txt"]

        with patch("os.path.isdir", return_value=False):
            self.completer.complete("/home/", 0)
            mock_glob.assert_called_with("/home/*")

    @patch("pebble_shell.utils.readline_support.readline")
    @patch("glob.glob")
    def test_complete_path_glob_error(
        self, mock_glob: Mock, mock_readline: Mock
    ) -> None:
        """Test handling glob errors in path completion."""
        mock_readline.get_line_buffer.return_value = "cat test"
        mock_glob.side_effect = OSError("Permission denied")

        result = self.completer.complete("test", 0)
        assert result is None

    @patch("pebble_shell.utils.readline_support.readline")
    def test_complete_exception_handling(self, mock_readline: Mock) -> None:
        """Test exception handling in complete method."""
        mock_readline.get_line_buffer.side_effect = Exception("readline error")

        result = self.completer.complete("test", 0)
        assert result is None

    def test_complete_command_filtering(self) -> None:
        """Test command name filtering."""
        matches = self.completer._complete_command("c")
        assert "cat" in matches
        assert "clear" in matches
        assert "ls" not in matches

    def test_complete_command_aliases(self) -> None:
        """Test alias completion."""
        matches = self.completer._complete_command("l")
        assert "ll" in matches
        assert "la" in matches
        assert "ls" in matches

    @patch("glob.glob")
    def test_complete_path_directories(self, mock_glob: Mock) -> None:
        """Test path completion with directories."""
        mock_glob.return_value = ["/home/dir", "/home/file.txt"]

        with patch("os.path.isdir") as mock_isdir:
            mock_isdir.side_effect = lambda path: path == "/home/dir"

            matches = self.completer._complete_path("/home/")
            assert "/home/dir/" in matches
            assert "/home/file.txt" in matches

    @patch("glob.glob")
    def test_complete_path_no_wildcard(self, mock_glob: Mock) -> None:
        """Test path completion without wildcard."""
        mock_glob.return_value = ["/home/test.txt"]

        with patch("os.path.isdir", return_value=False):
            self.completer._complete_path("/home/test")
            mock_glob.assert_called_with("/home/test*")


class TestSetupReadlineSupport:
    """Test setup_readline_support function."""

    @patch("pebble_shell.utils.readline_support.readline")
    @patch("builtins.print")
    def test_setup_with_readline(self, mock_print: Mock, mock_readline: Mock) -> None:
        """Test setup when readline is available."""
        commands = {"cat": Mock()}
        alias_command = Mock()
        shell = Mock()

        wrapper = setup_readline_support(commands, alias_command, shell)

        assert wrapper.has_readline
        mock_print.assert_called_with(
            "Enhanced readline support enabled (use tab for smart completion)"
        )

    @patch("pebble_shell.utils.readline_support.readline", None)
    @patch("builtins.print")
    def test_setup_no_readline(self, mock_print: Mock) -> None:
        """Test setup when readline is not available."""
        commands = {"cat": Mock()}
        alias_command = Mock()
        shell = Mock()

        wrapper = setup_readline_support(commands, alias_command, shell)

        assert not wrapper.has_readline
        mock_print.assert_called_with(
            "Readline not available (install 'readline' package for an enhanced experience)"
        )
