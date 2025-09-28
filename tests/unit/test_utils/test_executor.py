"""Tests for command executor functionality."""

from unittest.mock import MagicMock, Mock, patch

import ops
import pytest

from pebble_shell.utils.executor import CommandOutput, PipelineExecutor
from pebble_shell.utils.parser import CommandType, ParsedCommand


class TestCommandOutput:
    """Test cases for CommandOutput class."""

    @pytest.fixture
    def output(self):
        """Create CommandOutput instance."""
        return CommandOutput()

    def test_init(self, output):
        """Test output initialization."""
        assert output.exit_code == 0
        assert output.get_stdout() == ""
        assert output.get_stderr() == ""

    def test_write_stdout(self, output):
        """Test writing to stdout."""
        output.write_stdout("Hello")
        output.write_stdout(" World")
        assert output.get_stdout() == "Hello World"

    def test_write_stderr(self, output):
        """Test writing to stderr."""
        output.write_stderr("Error")
        output.write_stderr(" message")
        assert output.get_stderr() == "Error message"


class TestPipelineExecutor:
    """Test cases for PipelineExecutor class."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        mock_shell = Mock()
        mock_shell.client = Mock()
        mock_shell.console = Mock()
        return mock_shell

    @pytest.fixture
    def mock_commands(self):
        """Create mock command dictionary."""
        mock_cmd = Mock()
        mock_cmd.execute = Mock(return_value=0)
        mock_cmd.category = "Test Commands"
        mock_cmd.help = "Test command help"
        return {
            "ls": mock_cmd,
            "grep": mock_cmd,
            "wc": mock_cmd,
            "echo": mock_cmd,
        }

    @pytest.fixture
    def mock_alias_command(self):
        """Create mock alias command."""
        mock_alias = Mock()
        mock_alias.expand_alias = Mock(side_effect=lambda x: x)
        return mock_alias

    @pytest.fixture
    def executor(self, mock_commands, mock_alias_command, mock_shell):
        """Create PipelineExecutor instance."""
        return PipelineExecutor(mock_commands, mock_alias_command, mock_shell)

    def test_init(self, executor, mock_shell, mock_commands, mock_alias_command):
        """Test executor initialization."""
        assert executor.client is mock_shell.client
        assert executor.commands is mock_commands
        assert executor.alias_command is mock_alias_command

    def test_execute_simple_command(self, executor, mock_commands):
        """Test executing simple command."""
        cmd = ParsedCommand(command="echo", args=["hello"], type=CommandType.SIMPLE)

        # Mock the command to return success
        mock_commands["echo"].execute.return_value = 0

        result = executor.execute_pipeline([cmd])

        assert result is True
        mock_commands["echo"].execute.assert_called_once_with(
            executor.client, ["hello"]
        )

    def test_execute_exit_command(self, executor):
        """Test executing exit command."""
        cmd = ParsedCommand(command="exit", args=[], type=CommandType.SIMPLE)

        result = executor.execute_pipeline([cmd])

        assert result is False

    def test_execute_empty_pipeline(self, executor):
        """Test executing empty pipeline."""
        result = executor.execute_pipeline([])
        assert result is True

    def test_execute_unknown_command(self, executor, capsys):
        """Test executing unknown command."""
        cmd = ParsedCommand(command="unknown", args=[], type=CommandType.SIMPLE)

        result = executor.execute_pipeline([cmd])

        assert result is True
        captured = capsys.readouterr()
        assert "Command not found: unknown" in captured.err

    @patch("builtins.print")
    def test_execute_clear_command(self, mock_print, executor):
        """Test executing clear command."""
        cmd = ParsedCommand(command="clear", args=[], type=CommandType.SIMPLE)

        result = executor.execute_pipeline([cmd])

        assert result is True
        mock_print.assert_called_with("\033[2J\033[H", end="")

    def test_execute_and_success(self, executor, mock_commands):
        """Test AND operator with successful first command."""
        cmd1 = ParsedCommand(command="echo", args=["first"], type=CommandType.AND)
        cmd2 = ParsedCommand(command="echo", args=["second"], type=CommandType.SIMPLE)

        # Mock successful execution
        with patch.object(executor, "_execute_command_sequence", return_value=0):
            result = executor.execute_pipeline([cmd1, cmd2])

        assert result is True

    def test_execute_and_failure(self, executor, mock_commands):
        """Test AND operator with failed first command."""
        cmd1 = ParsedCommand(command="echo", args=["first"], type=CommandType.AND)
        cmd2 = ParsedCommand(command="echo", args=["second"], type=CommandType.SIMPLE)

        # Mock failed execution
        with patch.object(executor, "_execute_command_sequence", side_effect=[1, 0]):
            result = executor.execute_pipeline([cmd1, cmd2])

        assert result is True

    def test_execute_or_success(self, executor, mock_commands):
        """Test OR operator with successful first command."""
        cmd1 = ParsedCommand(command="echo", args=["first"], type=CommandType.OR)
        cmd2 = ParsedCommand(command="echo", args=["second"], type=CommandType.SIMPLE)

        # Mock successful execution
        with patch.object(executor, "_execute_command_sequence", return_value=0):
            result = executor.execute_pipeline([cmd1, cmd2])

        assert result is True

    def test_execute_or_failure(self, executor, mock_commands):
        """Test OR operator with failed first command."""
        cmd1 = ParsedCommand(command="echo", args=["first"], type=CommandType.OR)
        cmd2 = ParsedCommand(command="echo", args=["second"], type=CommandType.SIMPLE)

        # Mock failed execution for first, success for second
        with patch.object(executor, "_execute_command_sequence", side_effect=[1, 0]):
            result = executor.execute_pipeline([cmd1, cmd2])

        assert result is True

    def test_execute_semicolon(self, executor, mock_commands):
        """Test semicolon separator."""
        cmd1 = ParsedCommand(command="echo", args=["first"], type=CommandType.SEMICOLON)
        cmd2 = ParsedCommand(command="echo", args=["second"], type=CommandType.SIMPLE)

        # Both should execute regardless of exit codes
        with patch.object(executor, "_execute_command_sequence", side_effect=[1, 0]):
            result = executor.execute_pipeline([cmd1, cmd2])

        assert result is True

    @patch("pebble_shell.utils.executor.resolve_path")
    def test_write_to_file(self, mock_resolve_path, executor):
        """Test writing output to file."""
        mock_resolve_path.return_value = "/var/output.txt"

        executor._write_to_file("output.txt", "test content")

        executor.client.push.assert_called_once_with(
            "/var/output.txt", b"test content", make_dirs=True
        )

    @patch("pebble_shell.utils.executor.resolve_path")
    def test_write_to_file_append(self, mock_resolve_path, executor):
        """Test appending to file."""
        mock_resolve_path.return_value = "/var/output.txt"

        # Mock existing file content using MagicMock for context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b"existing "
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_context_manager.__exit__.return_value = None
        executor.client.pull.return_value = mock_context_manager

        executor._write_to_file("output.txt", "new content", append=True)

        executor.client.push.assert_called_once_with(
            "/var/output.txt", b"existing new content", make_dirs=True
        )

    @patch("pebble_shell.utils.executor.resolve_path")
    def test_read_from_file(self, mock_resolve_path, executor):
        """Test reading from file."""
        mock_resolve_path.return_value = "/var/input.txt"

        # Mock file content using MagicMock for context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b"file content"
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_file
        mock_context_manager.__exit__.return_value = None
        executor.client.pull.return_value = mock_context_manager

        content = executor._read_from_file("input.txt")

        assert content == "file content"
        executor.client.pull.assert_called_once_with("/var/input.txt")

    def test_handle_piped_sort(self, executor):
        """Test handling sort with piped input."""
        output = CommandOutput()
        cmd = ParsedCommand(command="sort", args=[], type=CommandType.SIMPLE)

        pipe_input = "zebra\napple\nbanana"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout()
        lines = result.strip().split("\n")
        assert lines == ["apple", "banana", "zebra"]

    def test_handle_piped_sort_reverse(self, executor):
        """Test handling sort -r with piped input."""
        output = CommandOutput()
        cmd = ParsedCommand(command="sort", args=["-r"], type=CommandType.SIMPLE)

        pipe_input = "zebra\napple\nbanana"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout()
        lines = result.strip().split("\n")
        assert lines == ["zebra", "banana", "apple"]

    def test_handle_piped_cut(self, executor):
        """Test handling cut with piped input."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="cut", args=["-f", "2", "-d", ":"], type=CommandType.SIMPLE
        )

        pipe_input = "user1:1000:group\nuser2:1001:group\nuser3:1002:group"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout()
        lines = result.strip().split("\n")
        assert lines == ["1000", "1001", "1002"]

    def test_handle_piped_cut_invalid_field(self, executor):
        """Test handling cut with invalid field specification."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="cut", args=["-f", "invalid"], type=CommandType.SIMPLE
        )

        pipe_input = "test line"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stderr()
        assert "invalid field specification" in result

    def test_handle_piped_cut_no_field_spec(self, executor):
        """Test handling cut without field specification."""
        output = CommandOutput()
        cmd = ParsedCommand(command="cut", args=[], type=CommandType.SIMPLE)

        pipe_input = "test line"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stderr()
        assert "field specification required" in result

    def test_handle_piped_grep_regex(self, executor):
        """Test handling grep with regex pattern."""
        output = CommandOutput()
        cmd = ParsedCommand(command="grep", args=["/^test/"], type=CommandType.SIMPLE)

        pipe_input = "test line\nanother line\ntest again"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout()
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert all(line.startswith("test") for line in lines)

    def test_handle_piped_grep_invalid_regex(self, executor):
        """Test handling grep with invalid regex."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="grep", args=["/[invalid/"], type=CommandType.SIMPLE
        )

        pipe_input = "test line"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stderr()
        assert "invalid pattern" in result

    def test_handle_piped_grep_no_pattern(self, executor):
        """Test handling grep without pattern."""
        output = CommandOutput()
        cmd = ParsedCommand(command="grep", args=[], type=CommandType.SIMPLE)

        pipe_input = "test line"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stderr()
        assert "missing pattern" in result

    def test_show_help(self, executor):
        """Test showing help information."""
        output = CommandOutput()

        executor._show_help(output)

        # The help method prints to the console, so check if console.print was called
        executor._shell.console.print.assert_called_once()

        # Check that the call was made with a Panel containing help info
        call_args = executor._shell.console.print.call_args[0][0]
        # The call should be with a Panel object containing help
        assert hasattr(call_args, "title")

    def test_skip_to_next_group(self, executor):
        """Test skipping to next command group."""
        commands = [
            ParsedCommand(command="echo", args=["1"], type=CommandType.AND),
            ParsedCommand(command="echo", args=["2"], type=CommandType.PIPE),
            ParsedCommand(command="echo", args=["3"], type=CommandType.SIMPLE),
            ParsedCommand(command="echo", args=["4"], type=CommandType.SIMPLE),
        ]

        # Should skip to command at index 2 (first SIMPLE after the AND command)
        next_index = executor._skip_to_next_group(commands, 0)
        assert next_index == 2

    def test_file_operations_error_handling(self, executor, capsys):
        """Test error handling in file operations."""
        executor.client.push.side_effect = Exception("Permission denied")

        # Should not raise exception
        executor._write_to_file("test.txt", "content")

        captured = capsys.readouterr()
        assert "Error writing to test.txt" in captured.err

    def test_read_file_error_handling(self, executor, capsys):
        """Test error handling when reading file."""
        executor.client.pull.side_effect = Exception("File not found")

        content = executor._read_from_file("nonexistent.txt")

        assert content == ""
        captured = capsys.readouterr()
        assert "Error reading from nonexistent.txt" in captured.err

    def test_handle_piped_wc(self, executor):
        """Test handling wc with piped input."""
        output = CommandOutput()
        cmd = ParsedCommand(command="wc", args=[], type=CommandType.SIMPLE)

        pipe_input = "line 1\nline 2\nline 3"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout()
        parts = result.strip().split()
        assert len(parts) == 3  # lines, words, chars
        assert parts[0] == "3"  # 3 lines

    def test_handle_piped_wc_lines_only(self, executor):
        """Test handling wc -l with piped input."""
        output = CommandOutput()
        cmd = ParsedCommand(command="wc", args=["-l"], type=CommandType.SIMPLE)

        pipe_input = "line 1\nline 2\nline 3"

        executor._handle_piped_text_command(cmd, pipe_input, output)

        result = output.get_stdout().rstrip()
        assert result == "       3"


class TestAdvancedExecutorCoverage:
    """Additional tests to improve executor coverage."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        mock_shell = Mock()
        mock_shell.client = Mock()
        mock_shell.console = Mock()
        mock_shell.commands = {"test": Mock()}
        return mock_shell

    @pytest.fixture
    def executor(self, mock_shell):
        """Create executor instance."""
        mock_commands = {"test": Mock()}
        mock_alias_command = Mock()
        return PipelineExecutor(mock_commands, mock_alias_command, mock_shell)

    def test_execute_pipeline_empty_list(self, executor):
        """Test executing an empty pipeline."""
        result = executor.execute_pipeline([])
        assert result is True

    def test_execute_command_sequence_simple(self, executor):
        """Test _execute_command_sequence with simple command."""
        cmd = ParsedCommand(command="echo", args=["hello"], type=CommandType.SIMPLE)

        with patch.object(executor, "_execute_single_command", return_value=0):
            exit_code = executor._execute_command_sequence(cmd)

        assert exit_code == 0

    def test_execute_pipeline_with_commands(self, executor):
        """Test _execute_pipeline with commands."""
        cmd1 = ParsedCommand(command="echo", args=["hello"], type=CommandType.SIMPLE)
        cmd2 = ParsedCommand(command="sort", args=[], type=CommandType.SIMPLE)

        with patch.object(executor, "_run_command", return_value=0):
            exit_code = executor._execute_pipeline([cmd1, cmd2])

        assert exit_code == 0

    def test_read_from_file_method(self, executor):
        """Test _read_from_file method."""
        mock_file = Mock()
        mock_file.read.return_value = b"test content"

        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_file)
        mock_context.__exit__ = Mock(return_value=None)
        executor.client.pull.return_value = mock_context

        result = executor._read_from_file("/test/file.txt")

        assert result == "test content"

    def test_read_from_file_error(self, executor):
        """Test _read_from_file with error."""
        executor.client.pull.side_effect = Exception("File not found")

        result = executor._read_from_file("/nonexistent.txt")

        assert result == ""

    def test_write_to_file_method(self, executor):
        """Test _write_to_file method."""
        executor._write_to_file("/test/test.txt", "hello world", append=False)

        executor.client.push.assert_called_once()

    def test_write_to_file_append_mode(self, executor):
        """Test _write_to_file with append mode."""
        # Mock existing content
        mock_file = Mock()
        mock_file.read.return_value = b"existing\n"

        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_file)
        mock_context.__exit__ = Mock(return_value=None)
        executor.client.pull.return_value = mock_context

        executor._write_to_file("/test/test.txt", "new content", append=True)

        executor.client.push.assert_called()

    def test_show_help_method(self, executor):
        """Test _show_help method."""
        output = CommandOutput()

        # Mock the commands with Mock objects that have category and help properties
        mock_cmd1 = Mock()
        mock_cmd1.category = "Test Category"
        mock_cmd1.help = "List files"

        mock_cmd2 = Mock()
        mock_cmd2.category = "Test Category"
        mock_cmd2.help = "Change directory"

        executor.commands = {"ls": mock_cmd1, "cd": mock_cmd2}

        # Mock the shell console to capture output
        with patch.object(executor._shell, "console") as mock_console:
            executor._show_help(output)
            # Should have called console.print to display help
            mock_console.print.assert_called_once()

    def test_skip_to_next_group_method(self, executor):
        """Test _skip_to_next_group method with current_index."""
        cmd1 = ParsedCommand(command="false", args=[], type=CommandType.AND)
        cmd2 = ParsedCommand(command="echo", args=["skipped"], type=CommandType.OR)
        cmd3 = ParsedCommand(command="echo", args=["executed"], type=CommandType.SIMPLE)

        cmd1.next_command = cmd2
        cmd2.next_command = cmd3

        commands = [cmd1, cmd2, cmd3]

        result = executor._skip_to_next_group(commands, 0)

        assert result == 2  # Should skip to index 2 (cmd3)

    def test_show_help_with_group_filter(self, executor):
        """Test _show_help method with group filter."""
        output = CommandOutput()

        # Mock commands with specific categories
        mock_cmd1 = Mock()
        mock_cmd1.category = "Test Category"
        mock_cmd1.help = "List files"

        executor.commands = {"ls": mock_cmd1}

        # Mock the shell console to capture output
        with patch.object(executor._shell, "console") as mock_console:
            executor._show_help(output, group="test")
            # Should have called console.print to display filtered help
            mock_console.print.assert_called_once()

    def test_show_help_no_matching_group(self, executor):
        """Test _show_help method with non-matching group filter."""
        output = CommandOutput()

        mock_cmd1 = Mock()
        mock_cmd1.category = "Other Category"
        mock_cmd1.help = "List files"

        executor.commands = {"ls": mock_cmd1}

        executor._show_help(output, group="nonexistent")

        # Should write error message to output
        assert "No command group found matching" in output.get_stdout()

    def test_show_help_command_without_category(self, executor):
        """Test _show_help method with command that raises NotImplementedError for category."""
        output = CommandOutput()

        mock_cmd = Mock()
        mock_cmd.category = Mock(side_effect=NotImplementedError)
        mock_cmd.help = "Test command"

        executor.commands = {"testcmd": mock_cmd}

        # Mock the shell console to capture output
        with patch.object(executor._shell, "console") as mock_console:
            executor._show_help(output)
            # Should still display help with "Other" category
            mock_console.print.assert_called_once()


class TestExecutorExceptionPaths:
    """Test exception and error handling paths in executor."""

    @pytest.fixture
    def mock_shell(self):
        """Create mock shell."""
        mock_shell = Mock()
        mock_shell.client = Mock()
        mock_shell.console = Mock()
        return mock_shell

    @pytest.fixture
    def executor(self, mock_shell):
        """Create executor instance."""
        mock_commands = {"test": Mock()}
        mock_alias_command = Mock()
        return PipelineExecutor(mock_commands, mock_alias_command, mock_shell)

    def test_run_command_with_input_redirection(self, executor):
        """Test _run_command with input redirection for text processing command."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="grep",
            args=["pattern"],
            type=CommandType.REDIRECT_IN,
            target="input.txt",
        )

        # Mock the grep command in executor.commands
        mock_command = Mock()
        executor.commands["grep"] = mock_command

        # Mock file reading
        with patch.object(executor, "_read_from_file", return_value="file content"):
            with patch.object(executor, "_handle_piped_text_command") as mock_handle:
                executor._run_command(cmd, None, output)
                mock_handle.assert_called_once_with(cmd, "file content", output)

    def test_run_command_with_input_redirection_regular_command(self, executor):
        """Test _run_command with input redirection for regular command."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="cat", args=[], type=CommandType.REDIRECT_IN, target="input.txt"
        )

        # Mock command and file reading
        mock_command = Mock()
        mock_command.execute.return_value = 0
        executor.commands["cat"] = mock_command

        with patch.object(executor, "_read_from_file", return_value="file content"):
            executor._run_command(cmd, None, output)

            # Should call regular command execution, not piped text command
            mock_command.execute.assert_called_once_with(executor.client, [])

    def test_run_command_help_with_args(self, executor):
        """Test help command with arguments."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="help", args=["filesystem"], type=CommandType.SIMPLE
        )

        with patch.object(executor, "_show_help") as mock_help:
            result = executor._run_command(cmd, None, output)
            mock_help.assert_called_once_with(output, group="filesystem")
            assert result == 0

    def test_run_command_path_error_exception(self, executor):
        """Test PathError exception handling."""
        output = CommandOutput()
        cmd = ParsedCommand(
            command="ls", args=["/nonexistent"], type=CommandType.SIMPLE
        )

        # Mock command to raise PathError
        mock_command = Mock()
        mock_command.execute.side_effect = ops.pebble.PathError("kind", "message")
        executor.commands["ls"] = mock_command

        result = executor._run_command(cmd, None, output)

        assert result == 1
        assert "Path error:" in output.get_stderr()

    def test_run_command_permission_error_exception(self, executor):
        """Test PermissionError exception handling."""
        output = CommandOutput()
        cmd = ParsedCommand(command="ls", args=["/restricted"], type=CommandType.SIMPLE)

        # Mock command to raise PermissionError
        mock_command = Mock()
        mock_command.execute.side_effect = PermissionError("Access denied")
        executor.commands["ls"] = mock_command

        result = executor._run_command(cmd, None, output)

        assert result == 1
        assert "Permission denied:" in output.get_stderr()

    def test_run_command_generic_exception(self, executor):
        """Test generic exception handling."""
        output = CommandOutput()
        cmd = ParsedCommand(command="test", args=[], type=CommandType.SIMPLE)

        # Mock command to raise generic exception
        mock_command = Mock()
        mock_command.execute.side_effect = RuntimeError("Something went wrong")
        executor.commands["test"] = mock_command

        result = executor._run_command(cmd, None, output)

        assert result == 1
        assert "Error executing command:" in output.get_stderr()

    def test_execute_single_command_redirect_out(self, executor):
        """Test single command with output redirection."""
        cmd = ParsedCommand(
            command="echo",
            args=["hello"],
            type=CommandType.REDIRECT_OUT,
            target="output.txt",
        )

        with patch.object(executor, "_run_command") as mock_run:
            with patch.object(executor, "_write_to_file") as mock_write:
                # Mock output content
                def capture_output(cmd, pipe_input, output):
                    output.write_stdout("hello\n")
                    return 0

                mock_run.side_effect = capture_output
                result = executor._execute_single_command(cmd)

                mock_write.assert_called_once_with(
                    "output.txt", "hello\n", append=False
                )
                assert result == 0

    def test_execute_single_command_redirect_append(self, executor):
        """Test single command with append redirection."""
        cmd = ParsedCommand(
            command="echo",
            args=["hello"],
            type=CommandType.REDIRECT_APPEND,
            target="output.txt",
        )

        with patch.object(executor, "_run_command") as mock_run:
            with patch.object(executor, "_write_to_file") as mock_write:
                # Mock output content
                def capture_output(cmd, pipe_input, output):
                    output.write_stdout("hello\n")
                    return 0

                mock_run.side_effect = capture_output
                result = executor._execute_single_command(cmd)

                mock_write.assert_called_once_with("output.txt", "hello\n", append=True)
                assert result == 0

    def test_execute_single_command_redirect_in(self, executor):
        """Test single command with input redirection."""
        cmd = ParsedCommand(
            command="cat", args=[], type=CommandType.REDIRECT_IN, target="input.txt"
        )

        with patch.object(executor, "_run_command", return_value=0) as mock_run:
            result = executor._execute_single_command(cmd)

            mock_run.assert_called_once()
            assert result == 0

    def test_execute_single_command_no_redirection_with_output(self, executor):
        """Test single command with no redirection but with stdout/stderr."""
        cmd = ParsedCommand(command="echo", args=["hello"], type=CommandType.SIMPLE)

        with patch.object(executor, "_run_command") as mock_run:
            with patch("builtins.print") as mock_print:
                # Mock output content
                def capture_output(cmd, pipe_input, output):
                    output.write_stdout("hello\n")
                    output.write_stderr("warning\n")
                    return 0

                mock_run.side_effect = capture_output
                result = executor._execute_single_command(cmd)

                # Should print both stdout and stderr
                assert mock_print.call_count == 2
                assert result == 0

    def test_execute_command_sequence_pipeline_with_pipe(self, executor):
        """Test command sequence with actual pipe."""
        cmd1 = ParsedCommand(command="echo", args=["hello"], type=CommandType.PIPE)
        cmd2 = ParsedCommand(command="sort", args=[], type=CommandType.SIMPLE)
        cmd1.next_command = cmd2

        with patch.object(
            executor, "_execute_pipeline", return_value=0
        ) as mock_pipeline:
            result = executor._execute_command_sequence(cmd1)

            mock_pipeline.assert_called_once()
            assert result == 0
