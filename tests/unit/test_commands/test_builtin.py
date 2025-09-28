"""Tests for builtin commands."""

from unittest.mock import MagicMock, Mock, patch

import ops
import pytest

from pebble_shell.commands.builtin import (
    CdCommand,
    CutCommand,
    EchoCommand,
    EnvCommand,
    GrepCommand,
    IdCommand,
    PwdCommand,
    SortCommand,
    UlimitCommand,
    WcCommand,
    WhoamiCommand,
)


class TestUlimitCommand:
    """Test cases for UlimitCommand."""

    @pytest.fixture
    def command(self):
        """Create UlimitCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return UlimitCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        # Mock /proc/self/limits content
        limits_content = """Limit                     Soft Limit           Hard Limit           Units
Max cpu time              unlimited            unlimited            seconds
Max file size             unlimited            unlimited            bytes
Max data size             unlimited            unlimited            bytes
Max stack size            8388608              unlimited            bytes
Max core file size        0                    unlimited            bytes
Max file descriptors      1024                 1048576              files
Max locked memory         67108864             67108864             bytes
"""

        mock_file.read.return_value = limits_content  # Return string, not bytes
        client.pull = MagicMock()
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
        return client

    def test_execute_show_all(self, command, mock_client):
        """Test ulimit command with -a option."""
        command.execute(mock_client, ["-a"])

        # Verify console output
        command.shell.console.print.assert_called()

    def test_execute_specific_limit(self, command, mock_client):
        """Test ulimit command with specific option."""
        command.execute(mock_client, ["-n"])

        # Verify console output
        command.shell.console.print.assert_called()

    def test_execute_error(self, command):
        """Test ulimit command with error."""
        client = Mock()
        client.pull.side_effect = Exception("Permission denied")

        command.execute(client, [])

        # Verify error message is printed
        command.shell.console.print.assert_called()


class TestSortCommand:
    """Test cases for SortCommand."""

    @pytest.fixture
    def command(self):
        """Create SortCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return SortCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        # Mock file content for sorting
        test_content = """zebra
apple
banana
cherry
"""

        mock_file.read.return_value = test_content  # Return string, not bytes
        client.pull = MagicMock()
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
        return client

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_basic_sort(self, mock_resolve_path, command, mock_client):
        """Test sort command basic functionality."""
        mock_resolve_path.return_value = "/test.txt"
        command.execute(mock_client, ["test.txt"])

        # Verify console output
        command.shell.console.print.assert_called()

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_reverse_sort(self, mock_resolve_path, command, mock_client):
        """Test sort command with reverse option."""
        mock_resolve_path.return_value = "/test.txt"
        command.execute(mock_client, ["-r", "test.txt"])

        # Verify console output
        command.shell.console.print.assert_called()

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_numeric_sort(self, mock_resolve_path, command, mock_client):
        """Test sort command with numeric option."""
        mock_resolve_path.return_value = "/numbers.txt"

        # Mock numeric content
        mock_file = MagicMock()
        numeric_content = "10\n2\n100\n3\n"
        mock_file.read.return_value = numeric_content  # Return string, not bytes
        mock_client.pull.return_value.__enter__.return_value = mock_file

        command.execute(mock_client, ["-n", "numbers.txt"])

        # Verify console output
        command.shell.console.print.assert_called()

    def test_execute_no_files(self, command, mock_client):
        """Test sort command with no files."""
        command.execute(mock_client, [])

        # Verify console output
        command.shell.console.print.assert_called()


class TestCutCommand:
    """Test cases for CutCommand."""

    @pytest.fixture
    def command(self):
        """Create CutCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return CutCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        # Mock CSV-like content
        test_content = """john:1000:users:/home/john:/bin/bash
jane:1001:users:/home/jane:/bin/bash
admin:0:root:/root:/bin/bash
"""

        mock_file.read.return_value = test_content  # Return string, not bytes
        client.pull.return_value = MagicMock()
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
        return client

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_extract_fields(self, mock_resolve_path, command, mock_client):
        """Test cut command extracting fields."""
        mock_resolve_path.return_value = "/passwd"
        command.execute(mock_client, ["-f", "1,3", "-d", ":", "passwd"])

        # Verify console output includes expected lines
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        output = "\n".join(output_lines)
        assert "john:users" in output
        assert "jane:users" in output
        assert "admin:root" in output

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_extract_characters(self, mock_resolve_path, command, mock_client):
        """Test cut command extracting characters."""
        mock_resolve_path.return_value = "/passwd"
        command.execute(mock_client, ["-c", "1-4", "passwd"])

        # Verify console output includes expected characters
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        output = "\n".join(output_lines)
        assert "john" in output
        assert "jane" in output
        assert "admi" in output

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_field_range(self, mock_resolve_path, command, mock_client):
        """Test cut command with field range."""
        mock_resolve_path.return_value = "/passwd"
        command.execute(mock_client, ["-f", "1-3", "-d", ":", "passwd"])

        # Verify console output includes expected field range
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        output = "\n".join(output_lines)
        assert "john:1000:users" in output

    def test_execute_no_files(self, command, mock_client):
        """Test cut command with no files."""
        command.execute(mock_client, ["-f", "1"])

        # Verify error message is printed
        command.shell.console.print.assert_called()

    def test_execute_no_field_spec(self, command, mock_client):
        """Test cut command without field specification."""
        command.execute(mock_client, ["file.txt"])

        # Verify error message is printed
        command.shell.console.print.assert_called()

    def test_parse_ranges(self, command):
        """Test range parsing."""
        # Single numbers
        assert command._parse_ranges("1,3,5") == [(1, 1), (3, 3), (5, 5)]

        # Ranges
        assert command._parse_ranges("1-3,5-7") == [(1, 3), (5, 7)]

        # Mixed
        assert command._parse_ranges("1,3-5,7") == [(1, 1), (3, 5), (7, 7)]

        # Invalid
        assert command._parse_ranges("invalid") is None

    def test_execute_insufficient_args(self, command, mock_client):
        """Test cut command with insufficient arguments."""
        command.execute(mock_client, ["-f"])

        # Verify error message is printed
        command.shell.console.print.assert_called()


class TestPwdCommand:
    """Test cases for PwdCommand."""

    @pytest.fixture
    def command(self):
        """Create PwdCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        mock_shell.current_directory = "/home/user"
        return PwdCommand(mock_shell)

    def test_execute(self, command):
        """Test pwd command."""
        command.execute(Mock(), [])

        # Verify console output
        command.shell.console.print.assert_called_with("/home/user")


class TestCdCommand:
    """Test cases for CdCommand."""

    @pytest.fixture
    def command(self):
        """Create CdCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        mock_shell.current_directory = "/"
        mock_shell.home_dir = "/home/user"
        return CdCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        client.list_files.return_value = []  # Valid directory
        return client

    @patch("pebble_shell.commands.builtin.get_shell_parser")
    def test_execute_absolute_path(
        self,
        mock_get_shell_parser,
        command,
        mock_client,
    ):
        """Test cd command with absolute path."""
        mock_parser = Mock()
        mock_get_shell_parser.return_value = mock_parser

        command.execute(mock_client, ["/home/user"])

        mock_client.list_files.assert_called_once_with("/home/user")
        assert command.shell.current_directory == "/home/user"
        mock_parser.update_pwd.assert_called_once_with("/home/user")

    @patch("pebble_shell.commands.builtin.get_shell_parser")
    def test_execute_relative_path(
        self,
        mock_get_shell_parser,
        command,
        mock_client,
    ):
        """Test cd command with relative path."""
        mock_parser = Mock()
        mock_get_shell_parser.return_value = mock_parser
        command.shell.current_directory = "/home"

        command.execute(mock_client, ["user"])

        mock_client.list_files.assert_called_once_with("/home/user")
        assert command.shell.current_directory == "/home/user"
        mock_parser.update_pwd.assert_called_once_with("/home/user")

    @patch("pebble_shell.commands.builtin.get_shell_parser")
    def test_execute_no_args(
        self,
        mock_get_shell_parser,
        command,
        mock_client,
    ):
        """Test cd command with no arguments."""
        mock_parser = Mock()
        mock_get_shell_parser.return_value = mock_parser

        command.execute(mock_client, [])

        # cd with no args should go to home directory (~)
        mock_client.list_files.assert_called_once_with("/home/user")  # shell.home_dir
        assert command.shell.current_directory == "/home/user"
        mock_parser.update_pwd.assert_called_once_with("/home/user")

    def test_execute_invalid_directory(self, command, mock_client):
        """Test cd command with invalid directory."""

        mock_client.list_files.side_effect = ops.pebble.APIError(
            {"message": "No such directory"}, 404, "status", "message"
        )

        result = command.execute(mock_client, ["/nonexistent"])

        # Should return error code
        assert result == 1
        # Should print error message
        command.shell.console.print.assert_called()
        # Should not change directory
        assert command.shell.current_directory == "/"  # unchanged from fixture

    def test_normalize_path(self, command):
        """Test path normalization."""
        assert command._normalise_path("/") == "/"
        assert command._normalise_path("/home/user") == "/home/user"
        assert command._normalise_path("/home/../root") == "/root"
        assert command._normalise_path("/home/./user") == "/home/user"
        assert command._normalise_path("/home/user/../..") == "/"


class TestEnvCommand:
    """Test cases for EnvCommand."""

    @pytest.fixture
    def command(self):
        """Create EnvCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return EnvCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        # Mock environment content (null-separated) - return as string as expected by the assertion
        env_content = "PATH=/bin:/usr/bin\x00HOME=/root\x00USER=root\x00"
        mock_file.read.return_value = env_content  # string, not bytes

        # Mock context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_file
        mock_context.__exit__.return_value = None
        client.pull.return_value = mock_context

        return client

    def test_execute_success(self, command, mock_client):
        """Test env command success."""
        result = command.execute(mock_client, [])

        # Should return success
        assert result == 0
        # Should call print (table will be in a Panel)
        command.shell.console.print.assert_called()
        # Verify that pull was called with expected paths
        assert mock_client.pull.call_count >= 1

    def test_execute_error(self, command):
        """Test env command with error."""
        client = Mock()
        client.pull.side_effect = ops.pebble.PathError("kind", "Permission denied")

        result = command.execute(client, [])

        # Should return error code
        assert result == 1
        # Should print error message
        command.shell.console.print.assert_called()


class TestWhoamiCommand:
    """Test cases for WhoamiCommand."""

    @pytest.fixture
    def command(self):
        """Create WhoamiCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return WhoamiCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()

            if path == "/proc/self/status":
                status_content = """Name:	bash
Umask:	0022
State:	S (sleeping)
Tgid:	1234
Ngid:	0
Pid:	1234
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
"""
                mock_file.read.return_value = status_content  # Return string, not bytes
            elif path == "/etc/passwd":
                passwd_content = """root:x:0:0:root:/root:/bin/bash
user:x:1000:1000:User:/home/user:/bin/bash
"""
                mock_file.read.return_value = passwd_content  # Return string, not bytes

            # Mock context manager properly
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        client.pull.side_effect = mock_pull
        return client

    def test_execute_success(self, command, mock_client):
        """Test whoami command success."""
        command.execute(mock_client, [])

        # Should call print with username
        command.shell.console.print.assert_called()
        # Check that a reasonable call was made (user info should be printed)
        assert mock_client.pull.call_count >= 1

    def test_execute_no_passwd(self, command):
        """Test whoami command without /etc/passwd."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()

            if path == "/proc/self/status":
                status_content = "Uid:	1000	1000	1000	1000\n"
                mock_file.read.return_value = status_content  # Return string, not bytes
            else:
                raise ops.pebble.PathError("kind", "File not found")

            # Mock context manager properly
            mock_context = MagicMock()
            mock_context.__enter__.return_value = mock_file
            mock_context.__exit__.return_value = None
            return mock_context

        client.pull.side_effect = mock_pull
        command.execute(client, [])

        # Should call print with uid info
        command.shell.console.print.assert_called()


class TestIdCommand:
    """Test cases for IdCommand."""

    @pytest.fixture
    def command(self):
        """Create IdCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return IdCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()

            if path == "/proc/self/status":
                status_content = """Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
"""
                mock_file.read.return_value = status_content  # Return string, not bytes
            elif path == "/etc/passwd":
                passwd_content = "user:x:1000:1000:User:/home/user:/bin/bash\n"
                mock_file.read.return_value = passwd_content  # Return string, not bytes
            elif path == "/etc/group":
                group_content = "user:x:1000:\n"
                mock_file.read.return_value = group_content  # Return string, not bytes

            return mock_file

        client.pull.side_effect = lambda path: MagicMock(
            __enter__=lambda _: mock_pull(path), __exit__=lambda *_: None
        )

        return client

    def test_execute_success(self, command, mock_client, capsys):
        """Test id command success."""
        command.execute(mock_client, [])

        # Check that console.print was called with the expected output
        command.console.print.assert_called_once()
        printed_text = command.console.print.call_args[0][0]
        assert "uid=1000(user)" in printed_text
        assert "gid=1000(user)" in printed_text


class TestEchoCommand:
    """Test cases for EchoCommand."""

    @pytest.fixture
    def command(self):
        """Create EchoCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return EchoCommand(mock_shell)

    def test_execute_simple_text(self, command, capsys):
        """Test echo command with simple text."""
        command.execute(Mock(), ["Hello", "World"])

        # Check that console.print was called with the expected output
        command.console.print.assert_called_once_with("Hello World")

    def test_execute_escape_sequences(self, command, capsys):
        """Test echo command with escape sequences."""
        command.execute(Mock(), ["Hello\\nWorld\\t!"])

        # Check that console.print was called with the expected output (escaped sequences processed)
        command.console.print.assert_called_once_with("Hello\nWorld\t!")

    def test_execute_no_args(self, command, capsys):
        """Test echo command with no arguments."""
        command.execute(Mock(), [])

        # Check that console.print was called with no arguments (empty line)
        command.console.print.assert_called_once_with()


class TestGrepCommand:
    """Test cases for GrepCommand."""

    @pytest.fixture
    def command(self):
        """Create GrepCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        mock_shell.current_directory = "/test/dir"
        mock_shell.home_dir = "/home/user"
        return GrepCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        test_content = """line 1: hello world
line 2: foo bar
line 3: hello again
line 4: goodbye world
"""

        mock_file.read.return_value = test_content  # Return string, not bytes
        client.pull = MagicMock()
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
        return client

    @patch("pebble_shell.commands.builtin.resolve_path")
    def test_execute_simple_pattern(self, mock_resolve_path, command, mock_client):
        """Test grep command with simple pattern."""
        mock_resolve_path.return_value = "/test/dir/test.txt"
        command.execute(mock_client, ["hello", "test.txt"])

        # Verify console output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        output = "\n".join(output_lines)
        assert "1:line 1: hello world" in output
        assert "3:line 3: hello again" in output
        assert "foo bar" not in output

    def test_execute_no_matches(self, command, mock_client, capsys):
        """Test grep command with no matches."""
        result = command.execute(mock_client, ["notfound", "test.txt"])

        captured = capsys.readouterr()
        assert captured.out.strip() == ""
        assert result == 1  # grep returns 1 when no matches

    def test_execute_regex_pattern(self, command, mock_client, capsys):
        """Test grep command with regex pattern."""
        command.execute(mock_client, ["/hello.*world/", "test.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("1:line 1: hello world" in line for line in output_lines)

    def test_execute_insufficient_args(self, command, mock_client, capsys):
        """Test grep command with insufficient arguments."""
        command.execute(mock_client, ["pattern"])

        # Check that console.print was called with usage message
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("Usage: grep" in line for line in output_lines)

    def test_execute_multiple_files(self, command, capsys):
        """Test grep command with multiple files."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()
            if "file1" in path:
                mock_file.read.return_value = (
                    "hello world\nfoo bar\n"  # Return string, not bytes
                )
            else:
                mock_file.read.return_value = (
                    "hello again\ngoodbye\n"  # Return string, not bytes
                )
            return mock_file

        client.pull.side_effect = lambda path: MagicMock(
            __enter__=lambda _: mock_pull(path), __exit__=lambda *_: None
        )

        command.execute(client, ["hello", "file1.txt", "file2.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("file1.txt:1:hello world" in line for line in output_lines)
        assert any("file2.txt:1:hello again" in line for line in output_lines)


class TestWcCommand:
    """Test cases for WcCommand."""

    @pytest.fixture
    def command(self):
        """Create WcCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        mock_shell.current_directory = "/test/dir"
        mock_shell.home_dir = "/home/user"
        return WcCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()
        mock_file = MagicMock()

        test_content = """line 1
line 2 with more words
line 3
"""

        mock_file.read.return_value = test_content  # Return string, not bytes
        client.pull = MagicMock()
        client.pull.return_value.__enter__.return_value = mock_file
        client.pull.return_value.__exit__.return_value = None
        return client

    def test_execute_default(self, command, mock_client, capsys):
        """Test wc command with default options."""
        command.execute(mock_client, ["test.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        # Should show lines, words, chars
        assert any("3" in line for line in output_lines)  # lines
        assert any("9" in line for line in output_lines)  # words (corrected count)
        assert any("test.txt" in line for line in output_lines)

    def test_execute_lines_only(self, command, mock_client, capsys):
        """Test wc command with -l option."""
        command.execute(mock_client, ["-l", "test.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("3" in line for line in output_lines)
        assert any("test.txt" in line for line in output_lines)

    def test_execute_words_only(self, command, mock_client, capsys):
        """Test wc command with -w option."""
        command.execute(mock_client, ["-w", "test.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("9" in line for line in output_lines)
        assert any("test.txt" in line for line in output_lines)

    def test_execute_chars_only(self, command, mock_client, capsys):
        """Test wc command with -c option."""
        command.execute(mock_client, ["-c", "test.txt"])

        # Check that console.print was called with the expected output
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        # Should show character count
        assert any("test.txt" in line for line in output_lines)

    def test_execute_no_files(self, command, mock_client, capsys):
        """Test wc command with no files."""
        command.execute(mock_client, [])

        # Check that console.print was called with usage message
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("Usage: wc" in line for line in output_lines)

    def test_execute_invalid_option(self, command, mock_client, capsys):
        """Test wc command with invalid option."""
        command.execute(mock_client, ["-x", "test.txt"])

        # Check that console.print was called with error message
        command.shell.console.print.assert_called()
        print_calls = command.shell.console.print.call_args_list
        output_lines = [str(call[0][0]) for call in print_calls]
        assert any("Invalid option" in line for line in output_lines)
