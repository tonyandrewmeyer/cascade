"""Tests for remote execution commands."""

from unittest.mock import Mock, patch

import pytest
from ops.pebble import ExecError

from pebble_shell.commands.exec_commands import (
    ExecCommand,
    RunCommand,
    ShellCommand,
    WhichCommand,
)


class TestExecCommand:
    """Test cases for ExecCommand."""

    @pytest.fixture
    def command(self):
        """Create ExecCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return ExecCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock Pebble client."""
        client = Mock()

        # Mock process
        mock_process = Mock()
        mock_process.wait_output.return_value = ("command output", "")
        mock_process.exit_code = 0

        client.exec.return_value = mock_process
        return client

    def test_execute_no_args(self, command, mock_client):
        """Test exec command with no arguments."""
        result = command.execute(mock_client, [])

        # Should print usage and return 0
        command.console.print.assert_any_call("Usage: exec <command> [args...]")
        assert result == 0

    def test_execute_simple_command(self, command, mock_client):
        """Test executing simple remote command."""
        command.execute(mock_client, ["echo", "hello"])

        # Should call exec with the command
        mock_client.exec.assert_called_once_with(["echo", "hello"])
        # Should call wait_output on the process
        mock_client.exec.return_value.wait_output.assert_called_once()

    def test_execute_interactive_mode(self, command, mock_client):
        """Test interactive mode execution."""
        command.execute(mock_client, ["-i", "/bin/bash"])

        mock_client.exec.assert_called_once()
        args, kwargs = mock_client.exec.call_args
        assert args[0] == ["/bin/bash"]
        # Interactive mode should have stdin/stdout/stderr set
        assert "stdin" in kwargs
        assert "stdout" in kwargs
        assert "stderr" in kwargs

    def test_execute_detached_mode(self, command, mock_client):
        """Test detached mode execution."""
        command.execute(mock_client, ["-d", "long_running_command"])

        mock_client.exec.assert_called_once()
        args, kwargs = mock_client.exec.call_args
        assert args[0] == ["long_running_command"]
        # In detached mode, stdin/stdout/stderr should be None
        assert kwargs.get("stdin") is None
        assert kwargs.get("stdout") is None
        assert kwargs.get("stderr") is None

    def test_execute_with_working_directory(self, command, mock_client):
        """Test execution with working directory."""
        # Note: working_dir is currently not supported by Pebble
        command.execute(mock_client, ["-w", "/var", "pwd"])

        mock_client.exec.assert_called_once()
        args, kwargs = mock_client.exec.call_args
        assert args[0] == ["pwd"]
        # working_dir is parsed but not passed to exec since it's not supported

    def test_execute_with_user(self, command, mock_client):
        """Test execution with specific user."""
        # Test in interactive mode where user option would be used
        command.execute(mock_client, ["-i", "-u", "testuser", "whoami"])

        mock_client.exec.assert_called_once()
        args, kwargs = mock_client.exec.call_args
        assert args[0] == ["whoami"]
        assert kwargs["user"] == "testuser"

    def test_execute_with_environment(self, command, mock_client):
        """Test execution with environment variables."""
        # Test in detached mode where environment option would be used
        command.execute(mock_client, ["-d", "-eTEST=value", "env"])

        mock_client.exec.assert_called_once()
        args, kwargs = mock_client.exec.call_args
        assert args[0] == ["env"]
        assert kwargs["environment"] == {"TEST": "value"}

    def test_execute_command_failure(self, command, mock_client):
        """Test handling command failure."""

        mock_client.exec.side_effect = ExecError(["false"], 1, "", "error message")

        result = command.execute(mock_client, ["false"])

        # Should print error and return 1
        assert result == 1

    def test_execute_with_exec_error(self, command, mock_client):
        """Test handling ExecError."""

        mock_client.exec.side_effect = ExecError(["failing_command"], 1, "out", "err")

        result = command.execute(mock_client, ["failing_command"])

        # Should return the error exit code
        assert result == 1


class TestRunCommand:
    """Test cases for RunCommand."""

    @pytest.fixture
    def command(self):
        """Create RunCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return RunCommand(mock_shell)

    def test_execute_no_args(self, command):
        """Test run command with no arguments."""
        result = command.execute(Mock(), [])

        command.console.print.assert_any_call("Usage: run <command> [args...]")
        assert result == 1

    @pytest.fixture
    def mock_client(self):
        """Create mock Pebble client."""
        return Mock()

    @patch("pebble_shell.commands.exec.ExecCommand")
    def test_execute_delegates_to_exec(self, mock_exec_class, command, mock_client):
        """Test that run delegates to exec command."""
        mock_exec_instance = Mock()
        mock_exec_class.return_value = mock_exec_instance

        command.execute(mock_client, ["ps", "aux"])

        mock_exec_class.assert_called_once_with(command.shell)
        mock_exec_instance.execute.assert_called_once_with(mock_client, ["ps", "aux"])


class TestShellCommand:
    """Test cases for ShellCommand."""

    @pytest.fixture
    def command(self):
        """Create ShellCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return ShellCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client for shell testing."""
        client = Mock()

        # Mock successful test for bash
        bash_process = Mock()
        bash_process.wait.return_value = None
        bash_process.exit_code = 0

        client.exec.return_value = bash_process
        return client

    @patch("pebble_shell.commands.exec.ExecCommand")
    def test_execute_finds_bash(self, mock_exec_class, command, mock_client):
        """Test finding and starting bash shell."""
        mock_exec_instance = Mock()
        mock_exec_class.return_value = mock_exec_instance

        # Mock successful test for bash
        bash_process = Mock()
        bash_process.wait.return_value = None
        mock_client.exec.return_value = bash_process

        command.execute(mock_client, [])

        # Should test for bash and then create ExecCommand
        mock_exec_class.assert_called_once_with(command.shell)
        mock_exec_instance.execute_remote_command.assert_called_once()

    def test_execute_no_shell_found(self, command):
        """Test when no shell is found."""
        client = Mock()

        # Mock all shell tests failing

        client.exec.side_effect = ExecError(["test"], 1, "", "")

        result = command.execute(client, [])

        # Should print error and return 1
        assert result == 1

    @patch("pebble_shell.commands.exec.ExecCommand")
    def test_execute_custom_shell(self, mock_exec_class, command, mock_client):
        """Test with custom shell specified."""
        mock_exec_instance = Mock()
        mock_exec_class.return_value = mock_exec_instance

        # Mock successful test for custom shell
        bash_process = Mock()
        bash_process.wait.return_value = None
        mock_client.exec.return_value = bash_process

        command.execute(mock_client, ["/bin/zsh"])

        mock_exec_class.assert_called_once_with(command.shell)
        mock_exec_instance.execute_remote_command.assert_called_once()


class TestWhichCommand:
    """Test cases for WhichCommand."""

    @pytest.fixture
    def command(self):
        """Create WhichCommand instance."""
        mock_shell = Mock()
        mock_shell.console = Mock()
        return WhichCommand(mock_shell)

    @pytest.fixture
    def mock_client(self):
        """Create mock client for which testing."""
        client = Mock()

        # Mock successful which command
        which_process = Mock()
        which_process.wait_output.return_value = ("/usr/bin/python3", "")
        which_process.exit_code = 0

        client.exec.return_value = which_process
        return client

    def test_execute_no_args(self, command):
        """Test which command with no arguments."""
        result = command.execute(Mock(), [])

        command.console.print.assert_any_call("Usage: which <command> [command2...]")
        assert result == 1

    def test_execute_finds_command(self, command, mock_client):
        """Test finding a command with which."""
        command.execute(mock_client, ["python3"])

        mock_client.exec.assert_called_with(["which", "python3"])

    def test_execute_command_not_found(self, command):
        """Test when command is not found."""

        client = Mock()
        client.exec.side_effect = ExecError(
            ["which", "nonexistent"], 1, "", "not found"
        )

        result = command.execute(client, ["nonexistent"])

        # Should return 1 for not found
        assert result == 1

    def test_execute_multiple_commands(self, command, mock_client):
        """Test finding multiple commands."""
        command.execute(mock_client, ["python3", "bash"])

        # Should call exec twice
        assert mock_client.exec.call_count == 2
