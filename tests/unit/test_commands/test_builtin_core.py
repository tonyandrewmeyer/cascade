"""Tests for core builtin commands."""

from unittest.mock import MagicMock, Mock

import pytest
from rich.console import Console

from pebble_shell.commands.builtin import (
    EchoCommand,
    PwdCommand,
    WhoamiCommand,
)


class TestEchoCommand:
    """Test cases for EchoCommand."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        shell = Mock()
        shell.console = Mock(spec=Console)
        return shell

    @pytest.fixture
    def command(self, mock_shell):
        """Create EchoCommand instance."""
        return EchoCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        return Mock()

    def _get_printed(self, command):
        """Extract the printed text from the mock console call."""
        call_args = command.shell.console.print.call_args
        return call_args[0][0] if call_args[0] else ""

    def _get_end(self, command):
        """Extract the end kwarg from the mock console call."""
        call_args = command.shell.console.print.call_args
        return call_args[1].get("end", "\n")

    def test_execute_simple_text(self, command, mock_client):
        """Test echo command with simple text."""
        result = command.execute(mock_client, ["hello", "world"])

        assert result == 0
        command.shell.console.print.assert_called_once_with(
            "hello world", end="\n", markup=False, highlight=False
        )

    def test_execute_no_args(self, command, mock_client):
        """Test echo command with no arguments outputs blank line."""
        result = command.execute(mock_client, [])

        assert result == 0
        command.shell.console.print.assert_called_once_with(
            "", end="\n", markup=False, highlight=False
        )

    def test_execute_escape_sequences(self, command, mock_client):
        """Test echo command with escape sequences (default -e)."""
        result = command.execute(mock_client, ["hello\\nworld"])

        assert result == 0
        assert self._get_printed(command) == "hello\nworld"

    def test_flag_n_suppresses_newline(self, command, mock_client):
        """Test -n flag suppresses trailing newline."""
        result = command.execute(mock_client, ["-n", "hello"])

        assert result == 0
        assert self._get_printed(command) == "hello"
        assert self._get_end(command) == ""

    def test_flag_upper_e_disables_escapes(self, command, mock_client):
        """Test -E flag disables escape interpretation."""
        result = command.execute(mock_client, ["-E", "hello\\nworld"])

        assert result == 0
        assert self._get_printed(command) == "hello\\nworld"

    def test_escape_c_stops_output(self, command, mock_client):
        """Test \\c stops all output including trailing newline."""
        result = command.execute(mock_client, ["hello\\cworld"])

        assert result == 0
        assert self._get_printed(command) == "hello"
        assert self._get_end(command) == ""

    def test_escape_octal(self, command, mock_client):
        """Test \\0nnn octal escape sequence."""
        result = command.execute(mock_client, ["\\0101"])

        assert result == 0
        assert self._get_printed(command) == "A"

    def test_escape_hex(self, command, mock_client):
        """Test \\xHH hex escape sequence."""
        result = command.execute(mock_client, ["\\x41"])

        assert result == 0
        assert self._get_printed(command) == "A"

    def test_flags_not_recognized_after_text(self, command, mock_client):
        """Test -n after text is treated as literal text."""
        result = command.execute(mock_client, ["foo", "-n"])

        assert result == 0
        assert self._get_printed(command) == "foo -n"
        assert self._get_end(command) == "\n"


class TestPwdCommand:
    """Test cases for PwdCommand."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        shell = Mock()
        shell.console = Mock(spec=Console)
        return shell

    @pytest.fixture
    def command(self, mock_shell):
        """Create PwdCommand instance."""
        return PwdCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        return Mock()

    def test_execute_prints_current_directory(self, command, mock_client):
        """Test pwd command prints current directory."""
        # Set up the shell's current_directory
        command.shell.current_directory = "/home/user"

        result = command.execute(mock_client, [])

        assert result == 0
        command.shell.console.print.assert_called_once_with("/home/user")


class TestWhoamiCommand:
    """Test cases for WhoamiCommand."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        shell = Mock()
        shell.console = Mock(spec=Console)
        return shell

    @pytest.fixture
    def command(self, mock_shell):
        """Create WhoamiCommand instance."""
        return WhoamiCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = Mock()

        def mock_pull(path):
            mock_file = MagicMock()
            if path == "/proc/self/status":
                status_content = """Name:	test_process
Umask:	0002
State:	S (sleeping)
Tgid:	1234
Ngid:	0
Pid:	1234
PPid:	1
TracerPid:	0
Uid:	1000	1000	1000	1000
Gid:	1000	1000	1000	1000
"""
                mock_file.read.return_value = status_content
            elif path == "/etc/passwd":
                passwd_content = """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
testuser:x:1000:1000:Test User:/home/testuser:/bin/bash
"""
                mock_file.read.return_value = passwd_content
            else:
                raise Exception("File not found")
            return mock_file

        # Create proper context manager mock
        def side_effect_func(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.return_value = mock_pull(path)
            mock_context_manager.__exit__.return_value = None
            return mock_context_manager

        client.pull.side_effect = side_effect_func
        return client

    def test_execute_success(self, command, mock_client):
        """Test whoami command successful execution."""
        result = command.execute(mock_client, [])

        assert result == 0
        # Should call pull twice: once for status, once for passwd
        assert mock_client.pull.call_count == 2
        mock_client.pull.assert_any_call("/proc/self/status")
        mock_client.pull.assert_any_call("/etc/passwd")
        command.shell.console.print.assert_called_once()
        # Check that the output contains uid and username information
        call_args = command.shell.console.print.call_args[0][0]
        assert "uid=1000(testuser)" in str(call_args)

    def test_execute_no_passwd_entry(self, command, mock_client):
        """Test whoami command when status file cannot be read."""

        def mock_pull_error(path):
            mock_context_manager = MagicMock()
            mock_context_manager.__enter__.side_effect = Exception("Permission denied")
            return mock_context_manager

        mock_client.pull.side_effect = mock_pull_error

        # Expect the exception to be raised since WhoamiCommand doesn't catch it
        with pytest.raises(Exception, match="Permission denied"):
            command.execute(mock_client, [])
