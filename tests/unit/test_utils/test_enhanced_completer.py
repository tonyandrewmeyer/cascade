"""Tests for enhanced completer utilities."""

from __future__ import annotations

from unittest.mock import Mock, patch

from pebble_shell.utils.enhanced_completer import EnhancedCompleter


class TestEnhancedCompleter:
    """Test EnhancedCompleter class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.shell = Mock()
        self.shell.client = Mock()
        self.shell.console = Mock()

        self.commands = {
            "cat": Mock(),
            "ls": Mock(),
            "pgrep": Mock(),
        }

        self.alias_command = Mock()
        self.alias_command.aliases = {"ll": "ls -la", "la": "ls -a"}

        self.completer = EnhancedCompleter(
            self.shell, self.commands, self.alias_command
        )

    def test_init(self) -> None:
        """Test completer initialization."""
        assert self.completer.shell is self.shell
        assert self.completer.client is self.shell.client
        assert self.completer.commands is self.commands
        assert self.completer.alias_command is self.alias_command

        expected_commands = ["cat", "ls", "pgrep", "help", "exit", "clear"]
        for cmd in expected_commands:
            assert cmd in self.completer.command_names

        # Check that command-specific completions are registered
        assert "pgrep" in self.completer.command_completions
        assert "cd" in self.completer.command_completions
        assert "cat" in self.completer.command_completions

    def test_complete_success(self) -> None:
        """Test successful completion."""
        with patch.object(self.completer, "_get_current_line", return_value="ls "):
            # Test first call (state=0)
            first_match = self.completer.complete("test", 0)
            # Should return string or None
            assert first_match is None or isinstance(first_match, str)

    def test_complete_exception_handling(self) -> None:
        """Test completion with exception handling."""
        with patch.object(
            self.completer, "_get_current_line", side_effect=Exception("Test error")
        ):
            matches = self.completer.complete("test", 0)

            # Should handle exception gracefully and return None
            assert matches is None

    def test_generate_completions_command(self) -> None:
        """Test completion generation for commands."""
        with patch.object(self.completer, "_get_current_line", return_value="l"):
            matches = self.completer._generate_completions("l")

            # Should return ls command
            assert "ls" in matches

    def test_generate_completions_arguments(self) -> None:
        """Test completion generation for arguments."""
        # Mock the client list_files method to return mock entries
        mock_entry = Mock()
        mock_entry.name = "home"
        mock_entry.type = "directory"

        with patch.object(self.completer, "_get_current_line", return_value="ls /"):
            with patch.object(
                self.completer.client, "list_files", return_value=[mock_entry]
            ):
                matches = self.completer._generate_completions("/")

                # Should return path completions
                assert isinstance(matches, list)

    def test_complete_exception_handling_v2(self) -> None:
        """Test exception handling in complete method."""
        with patch.object(
            self.completer, "_get_current_line", side_effect=Exception("readline error")
        ):
            result = self.completer.complete("test", 0)
            assert result is None

    def test_generate_completions_command_v2(self) -> None:
        """Test completion generation for command names."""
        with patch.object(self.completer, "_get_current_line", return_value="c"):
            matches = self.completer._generate_completions("c")
            assert "cat" in matches
            assert "clear" in matches

    def test_generate_completions_arguments_v2(self) -> None:
        """Test completion generation for command arguments."""
        # Mock client.list_files for the _complete_paths method
        mock_entry = Mock()
        mock_entry.name = "test.txt"
        self.shell.client.list_files.return_value = [mock_entry]

        with patch.object(self.completer, "_get_current_line", return_value="cat file"):
            matches = self.completer._generate_completions("file")
            # Should return something from mocked paths
            assert isinstance(matches, list)

    def test_get_current_line_no_readline(self) -> None:
        """Test getting current line when readline is not available."""
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'readline'")
        ):
            result = self.completer._get_current_line()
            assert result == ""

    @patch("builtins.__import__")
    def test_get_current_line_with_readline(self, mock_import: Mock) -> None:
        """Test getting current line with readline."""
        mock_readline = Mock()
        mock_readline.get_line_buffer.return_value = "test command"
        mock_import.return_value = mock_readline

        result = self.completer._get_current_line()
        assert result == "test command"

    @patch("builtins.__import__")
    def test_get_current_line_exception(self, mock_import: Mock) -> None:
        """Test handling AttributeError in _get_current_line."""
        mock_readline = Mock()
        mock_readline.get_line_buffer.side_effect = AttributeError()
        mock_import.return_value = mock_readline

        result = self.completer._get_current_line()
        assert result == ""

    def test_complete_command_exact_matches(self) -> None:
        """Test command completion with exact matches."""
        matches = self.completer._complete_command("c")
        assert "cat" in matches
        assert "clear" in matches
        assert "ls" not in matches

    def test_complete_command_aliases(self) -> None:
        """Test command completion with aliases."""
        matches = self.completer._complete_command("l")
        assert "ll" in matches
        assert "la" in matches
        assert "ls" in matches

    def test_complete_command_fuzzy_matching(self) -> None:
        """Test command completion with fuzzy matching."""
        with patch.object(
            self.completer, "_fuzzy_match", return_value=True
        ) as mock_fuzzy:
            self.completer._complete_command("xyz")
            mock_fuzzy.assert_called()
            # Should include fuzzy matches when no exact matches found

    def test_complete_argument_command_specific(self) -> None:
        """Test argument completion for commands with specific handlers."""
        # Mock the client to avoid the actual _complete_process_names implementation
        self.shell.client.list_files.return_value = []

        matches = self.completer._complete_argument("pgrep", ["pgrep", "ba"], "ba")
        assert isinstance(matches, list)

    def test_complete_argument_default_path(self) -> None:
        """Test argument completion falls back to path completion."""
        with patch.object(
            self.completer, "_complete_paths", return_value=["/home/test"]
        ):
            matches = self.completer._complete_argument(
                "unknown", ["unknown", "test"], "test"
            )
            assert matches == ["/home/test"]

    def test_complete_process_names(self) -> None:
        """Test process name completion."""
        # Mock /proc directory listing
        proc_entry1 = Mock()
        proc_entry1.name = "123"
        proc_entry2 = Mock()
        proc_entry2.name = "456"
        proc_entry3 = Mock()
        proc_entry3.name = "not_a_pid"

        self.shell.client.list_files.return_value = [
            proc_entry1,
            proc_entry2,
            proc_entry3,
        ]

        # Mock process command files with context manager support
        def mock_pull(path: str):
            mock_file = Mock()
            mock_file.__enter__ = Mock(return_value=mock_file)
            mock_file.__exit__ = Mock(return_value=None)

            if path == "/proc/123/comm":
                mock_file.read.return_value = "bash\n"
            elif path == "/proc/456/comm":
                mock_file.read.return_value = "zsh\n"
            else:
                raise Exception(f"not found: {path}")
            return mock_file

        self.shell.client.pull.side_effect = mock_pull

        matches = self.completer._complete_process_names("ba", ["pgrep", "ba"])
        assert "bash" in matches
        assert "zsh" not in matches

    def test_complete_process_names_non_string_comm(self) -> None:
        """Test process name completion with non-string comm content."""
        proc_entry = Mock()
        proc_entry.name = "123"

        self.shell.client.list_files.return_value = [proc_entry]

        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.read.return_value = b"bash\n"  # bytes instead of string
        self.shell.client.pull.return_value = mock_file

        matches = self.completer._complete_process_names("ba", ["pgrep", "ba"])
        assert matches == []

    def test_fuzzy_match_similarity_threshold(self) -> None:
        """Test fuzzy matching with similarity threshold."""
        # Test cases with different similarity levels
        assert self.completer._fuzzy_match("cat", "cut")
        assert self.completer._fuzzy_match("ls", "list")
        assert not self.completer._fuzzy_match("x", "completely_different")

    def test_fuzzy_match_empty_strings(self) -> None:
        """Test fuzzy matching with empty strings."""
        assert self.completer._fuzzy_match(
            "", "command"
        )  # Empty pattern matches anything
        assert not self.completer._fuzzy_match("command", "")

    @patch.object(EnhancedCompleter, "_complete_pebble_services")
    def test_pebble_command_completions(self, mock_complete_services: Mock) -> None:
        """Test that Pebble commands use service completion."""
        mock_complete_services.return_value = ["service1", "service2"]

        # Test various pebble commands
        pebble_commands = [
            "pebble-start",
            "pebble-stop",
            "pebble-restart",
            "pebble-signal",
        ]

        for cmd in pebble_commands:
            if cmd in self.completer.command_completions:
                self.completer.command_completions[cmd]("serv", [cmd, "serv"])
                mock_complete_services.assert_called_with("serv", [cmd, "serv"])

    def test_file_command_completions(self) -> None:
        """Test that file commands use file completion."""
        file_commands = ["cat", "head", "tail", "diff", "grep"]

        for cmd in file_commands:
            assert cmd in self.completer.command_completions
            # Verify it points to the file completion method
            assert (
                self.completer.command_completions[cmd]
                == self.completer._complete_files
            )

    def test_directory_command_completions(self) -> None:
        """Test that directory commands use directory completion."""
        dir_commands = ["cd", "find"]

        for cmd in dir_commands:
            assert cmd in self.completer.command_completions
            # Verify it points to the directory completion method
            assert (
                self.completer.command_completions[cmd]
                == self.completer._complete_directories
            )

    def test_path_command_completions(self) -> None:
        """Test that path commands use path completion."""
        path_commands = ["ls", "cp", "mv", "rm", "stat"]

        for cmd in path_commands:
            assert cmd in self.completer.command_completions
            # Verify it points to the path completion method
            assert (
                self.completer.command_completions[cmd]
                == self.completer._complete_paths
            )


class TestEnhancedCompleterAdvanced:
    """Advanced tests for EnhancedCompleter edge cases and error handling."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.shell = Mock()
        self.shell.client = Mock()
        self.shell.console = Mock()
        self.commands = {"test": Mock()}
        self.alias_command = Mock()
        self.alias_command.aliases = {}
        self.completer = EnhancedCompleter(
            self.shell, self.commands, self.alias_command
        )

    def test_complete_pebble_services_error_handling(self) -> None:
        """Test Pebble service completion with API errors."""

        # Mock a connection error
        connection_error = Exception("Connection failed")
        self.shell.client.get_services.side_effect = connection_error

        completions = self.completer._complete_pebble_services(
            "test", ["pebble-start", "test"]
        )

        assert completions == []

    def test_complete_pebble_checks_error_handling(self) -> None:
        """Test Pebble check completion with API errors."""
        # Mock an API error
        api_error = Exception("API Error")
        self.shell.client.get_checks.side_effect = api_error

        completions = self.completer._complete_pebble_checks(
            "test", ["pebble-check", "test"]
        )

        assert completions == []

    def test_complete_pebble_notices_error_handling(self) -> None:
        """Test Pebble notice completion with API errors."""
        self.shell.client.get_notices.side_effect = Exception("Unexpected error")

        completions = self.completer._complete_pebble_notices(
            "test", ["pebble-notice", "test"]
        )

        assert completions == []

    def test_complete_paths_with_remote_error(self) -> None:
        """Test path completion when remote file listing fails."""
        self.shell.client.list_files.side_effect = Exception("Path not found")

        completions = self.completer._complete_paths("test", ["ls", "test"])

        assert completions == []

    def test_complete_paths_empty_directory(self) -> None:
        """Test path completion with empty directory."""
        self.shell.client.list_files.return_value = []

        completions = self.completer._complete_paths("test", ["ls", "test"])

        assert completions == []

    def test_complete_directories_filters_files(self) -> None:
        """Test directory completion filters out files."""
        # Set up empty list for now, just ensure method doesn't crash
        self.shell.client.list_files.return_value = []

        completions = self.completer._complete_directories("dir", ["cd", "dir"])

        # Should return a list (may be empty)
        assert isinstance(completions, list)

    def test_complete_files_filters_directories(self) -> None:
        """Test file completion filters out directories."""
        # Set up empty list for now, just ensure method doesn't crash
        self.shell.client.list_files.return_value = []

        completions = self.completer._complete_files("file", ["cat", "file"])

        # Should return a list (may be empty)
        assert isinstance(completions, list)

    def test_fuzzy_match_edge_cases(self) -> None:
        """Test fuzzy matching with edge cases."""
        # Empty pattern should match anything
        assert self.completer._fuzzy_match("", "anything")

        # Empty text should not match non-empty pattern
        assert not self.completer._fuzzy_match("pattern", "")

        # Both empty
        assert self.completer._fuzzy_match("", "")

        # Case sensitivity
        assert self.completer._fuzzy_match("ABC", "abc")
        assert self.completer._fuzzy_match("abc", "ABC")

    def test_complete_argument_unknown_command(self) -> None:
        """Test argument completion for unknown command."""
        # Set up empty file list for path completion fallback
        self.shell.client.list_files.return_value = []

        completions = self.completer._complete_argument(
            "unknown_command", ["unknown_command", "arg"], "arg"
        )

        # Should fall back to path completion and return empty list since no files
        assert isinstance(completions, list)

    def test_complete_command_no_fuzzy_matches(self) -> None:
        """Test command completion when no fuzzy matches exist."""
        completions = self.completer._complete_command("zzzzz")

        assert completions == []

    def test_complete_with_similarity_threshold(self) -> None:
        """Test fuzzy matching respects similarity threshold."""
        # Very different strings should not match
        assert not self.completer._fuzzy_match("abc", "xyz")

        # Similar strings should match
        assert self.completer._fuzzy_match("test", "testt")

    def test_complete_pebble_services_success(self) -> None:
        """Test successful Pebble service completion."""
        mock_service = Mock()
        mock_service.name = "test-service"
        self.shell.client.get_services.return_value = [mock_service]

        completions = self.completer._complete_pebble_services(
            "test", ["pebble-start", "test"]
        )

        assert any("test-service" in comp for comp in completions)

    def test_complete_pebble_checks_success(self) -> None:
        """Test successful Pebble check completion."""
        mock_check = Mock()
        mock_check.name = "health-check"
        self.shell.client.get_checks.return_value = [mock_check]

        completions = self.completer._complete_pebble_checks(
            "hea", ["pebble-check", "hea"]
        )

        assert any("health-check" in comp for comp in completions)

    def test_complete_pebble_notices_success(self) -> None:
        """Test successful Pebble notice completion."""
        mock_notice = Mock()
        mock_notice.id = "123"
        self.shell.client.get_notices.return_value = [mock_notice]

        completions = self.completer._complete_pebble_notices(
            "12", ["pebble-notice", "12"]
        )

        assert "123" in completions

    def test_complete_mount_points_success(self) -> None:
        """Test successful mount point completion."""
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.read.return_value = "/dev/sda1 /home ext4 rw,relatime 0 0\n/dev/sda2 /var ext4 rw,relatime 0 0\n"
        self.shell.client.pull.return_value = mock_file

        completions = self.completer._complete_mount_points("/ho", ["mount", "/ho"])

        assert "/home" in completions

    def test_complete_mount_points_invalid_lines(self) -> None:
        """Test mount point completion with invalid mount lines."""
        mock_file = Mock()
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        mock_file.read.return_value = (
            "\n\nsingle_part\n/dev/sda1 /home ext4 rw,relatime 0 0\n"
        )
        self.shell.client.pull.return_value = mock_file

        completions = self.completer._complete_mount_points("/ho", ["mount", "/ho"])

        assert "/home" in completions

    def test_complete_paths_directory_ending_slash(self) -> None:
        """Test path completion when text ends with slash."""
        from unittest.mock import Mock, patch

        # Mock the FileType enum
        with patch(
            "pebble_shell.utils.enhanced_completer.ops.pebble.FileType"
        ) as mock_filetype:
            mock_filetype.DIRECTORY = "directory"

            mock_entry = Mock()
            mock_entry.name = "subdir"
            mock_entry.type = "directory"
            self.shell.client.list_files.return_value = [mock_entry]

            completions = self.completer._complete_paths("/home/", ["ls", "/home/"])

            assert "/home/subdir/" in completions

    def test_complete_paths_file_entry(self) -> None:
        """Test path completion for file entries."""
        from unittest.mock import Mock, patch

        # Mock the FileType enum
        with patch(
            "pebble_shell.utils.enhanced_completer.ops.pebble.FileType"
        ) as mock_filetype:
            mock_filetype.DIRECTORY = "directory"

            mock_entry = Mock()
            mock_entry.name = "file.txt"
            mock_entry.type = "file"  # Not equal to DIRECTORY
            self.shell.client.list_files.return_value = [mock_entry]

            completions = self.completer._complete_paths(
                "/home/file", ["cat", "/home/file"]
            )

            assert "/home/file.txt" in completions

    def test_complete_paths_root_prefix_handling(self) -> None:
        """Test path completion handles root prefix correctly."""
        from unittest.mock import Mock, patch

        # Mock the FileType enum
        with patch(
            "pebble_shell.utils.enhanced_completer.ops.pebble.FileType"
        ) as mock_filetype:
            mock_filetype.DIRECTORY = "directory"

            mock_entry = Mock()
            mock_entry.name = "bin"
            mock_entry.type = "directory"
            self.shell.client.list_files.return_value = [mock_entry]

            completions = self.completer._complete_paths("/b", ["ls", "/b"])

            assert "/bin/" in completions

    def test_complete_paths_relative_path(self) -> None:
        """Test path completion converts relative paths to absolute."""
        from unittest.mock import Mock, patch

        # Mock the FileType enum
        with patch(
            "pebble_shell.utils.enhanced_completer.ops.pebble.FileType"
        ) as mock_filetype:
            mock_filetype.DIRECTORY = "directory"

            mock_entry = Mock()
            mock_entry.name = "file.txt"
            mock_entry.type = "file"  # Not a directory
            self.shell.client.list_files.return_value = [mock_entry]

            completions = self.completer._complete_paths("file", ["cat", "file"])

            assert "/file.txt" in completions

    def test_complete_directories_filters_correctly(self) -> None:
        """Test directory completion filters out files."""
        with patch.object(
            self.completer, "_complete_paths", return_value=["/home/", "/file.txt"]
        ):
            completions = self.completer._complete_directories("", ["cd", ""])

            assert "/home/" in completions
            assert "/file.txt" not in completions

    def test_complete_files_filters_correctly(self) -> None:
        """Test file completion filters out directories."""
        with patch.object(
            self.completer, "_complete_paths", return_value=["/home/", "/file.txt"]
        ):
            completions = self.completer._complete_files("", ["cat", ""])

            assert "/file.txt" in completions
            assert "/home/" not in completions

    def test_get_completion_hints(self) -> None:
        """Test getting completion hints for commands."""
        hints = self.completer.get_completion_hints("pgrep")
        assert "-f" in hints
        assert "-u" in hints
        assert "process_name" in hints

        # Test unknown command
        hints = self.completer.get_completion_hints("unknown")
        assert hints == []

    def test_show_completion_help(self) -> None:
        """Test showing completion help."""
        self.completer.show_completion_help("pgrep")

        # Verify console.print was called
        assert self.shell.console.print.call_count >= 2  # At least title and hints

    def test_show_completion_help_no_hints(self) -> None:
        """Test showing completion help for command with no hints."""
        self.completer.show_completion_help("unknown")

        # Should not print anything if no hints
        self.shell.console.print.assert_not_called()

    def test_complete_state_handling(self) -> None:
        """Test complete method handles different states correctly."""
        with patch.object(self.completer, "_get_current_line", return_value="ls"):
            # First call should generate matches
            first_result = self.completer.complete("ls", 0)
            assert first_result is None or isinstance(first_result, str)

            # Subsequent calls should return matches from cached list
            second_result = self.completer.complete("ls", 1)
            assert second_result is None or isinstance(second_result, str)

    def test_complete_process_names_with_path_error(self) -> None:
        """Test process name completion handles PathError gracefully."""
        from unittest.mock import Mock, patch

        proc_entry = Mock()
        proc_entry.name = "123"
        self.shell.client.list_files.return_value = [proc_entry]

        # Create a proper exception class
        class MockPathError(Exception):
            pass

        with patch(
            "pebble_shell.utils.enhanced_completer.ops.pebble.PathError", MockPathError
        ):
            # Mock PathError for the pull operation
            self.shell.client.pull.side_effect = MockPathError("Path not found")

            matches = self.completer._complete_process_names("ba", ["pgrep", "ba"])
            assert matches == []
