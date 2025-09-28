"""Tests for shell parser functionality."""

from unittest.mock import patch

import pytest

from pebble_shell.utils.parser import (
    CommandType,
    ShellParser,
    ShellVariables,
    get_shell_parser,
    init_shell_parser,
)


class TestShellVariables:
    """Test cases for ShellVariables class."""

    @pytest.fixture
    def variables(self):
        """Create ShellVariables instance."""
        return ShellVariables()

    def test_init_default_variables(self, variables):
        """Test initialization with default variables."""
        assert variables.get_variable("PWD") == "/"
        assert variables.get_variable("USER") == "root"
        assert variables.get_variable("HOME") == "/root"
        assert variables.get_variable("?") == "0"

    def test_set_and_get_variable(self, variables):
        """Test setting and getting variables."""
        variables.set_variable("MYVAR", "myvalue")
        assert variables.get_variable("MYVAR") == "myvalue"

    def test_get_nonexistent_variable(self, variables):
        """Test getting non-existent variable."""
        assert variables.get_variable("NONEXISTENT") == ""

    @patch("os.environ.get")
    def test_get_environment_variable(self, mock_env_get, variables):
        """Test getting environment variable."""
        mock_env_get.return_value = "env_value"
        assert variables.get_variable("ENV_VAR") == "env_value"
        mock_env_get.assert_called_once_with("ENV_VAR", "")

    def test_expand_variables_simple(self, variables):
        """Test simple variable expansion."""
        variables.set_variable("USER", "testuser")
        result = variables.expand_variables("Hello $USER")
        assert result == "Hello testuser"

    def test_expand_variables_braced(self, variables):
        """Test braced variable expansion."""
        variables.set_variable("USER", "testuser")
        result = variables.expand_variables("Hello ${USER}!")
        assert result == "Hello testuser!"

    def test_expand_variables_multiple(self, variables):
        """Test multiple variable expansion."""
        variables.set_variable("USER", "testuser")
        variables.set_variable("HOME", "/home/test")
        result = variables.expand_variables("$USER lives in $HOME")
        assert result == "testuser lives in /home/test"

    def test_expand_variables_no_expansion(self, variables):
        """Test text with no variables."""
        result = variables.expand_variables("No variables here")
        assert result == "No variables here"

    def test_expand_variables_nonexistent(self, variables):
        """Test expansion of non-existent variable."""
        result = variables.expand_variables("Hello $NONEXISTENT")
        assert result == "Hello "

    def test_update_pwd(self, variables):
        """Test updating PWD variable."""
        variables.update_pwd("/new/path")
        assert variables.get_variable("PWD") == "/new/path"

    def test_exit_code_variable(self, variables):
        """Test exit code special variable."""
        variables.last_exit_code = 42
        assert variables.get_variable("?") == "42"


class TestShellParser:
    """Test cases for ShellParser class."""

    @pytest.fixture
    def parser(self):
        """Create ShellParser instance."""
        return ShellParser()

    def test_init(self, parser):
        """Test parser initialization."""
        assert parser.variables is not None
        assert isinstance(parser.variables, ShellVariables)

    def test_parse_simple_command(self, parser):
        """Test parsing simple command."""
        commands = parser.parse_command_line("ls -la")

        assert len(commands) == 1
        assert commands[0].command == "ls"
        assert commands[0].args == ["-la"]
        assert commands[0].type == CommandType.SIMPLE

    def test_parse_empty_command(self, parser):
        """Test parsing empty command."""
        commands = parser.parse_command_line("")
        assert len(commands) == 0

    def test_parse_pipe_commands(self, parser):
        """Test parsing piped commands."""
        commands = parser.parse_command_line("ps | grep python")

        assert len(commands) == 2
        assert commands[0].command == "ps"
        assert commands[0].type == CommandType.PIPE
        assert commands[0].next_command == commands[1]
        assert commands[1].command == "grep"
        assert commands[1].args == ["python"]

    def test_parse_output_redirection(self, parser):
        """Test parsing output redirection."""
        commands = parser.parse_command_line("ls > output.txt")

        assert len(commands) == 1
        assert commands[0].command == "ls"
        assert commands[0].type == CommandType.REDIRECT_OUT
        assert commands[0].target == "output.txt"

    def test_parse_append_redirection(self, parser):
        """Test parsing append redirection."""
        commands = parser.parse_command_line("echo hello >> log.txt")

        assert len(commands) == 1
        assert commands[0].command == "echo"
        assert commands[0].args == ["hello"]
        assert commands[0].type == CommandType.REDIRECT_APPEND
        assert commands[0].target == "log.txt"

    def test_parse_input_redirection(self, parser):
        """Test parsing input redirection."""
        commands = parser.parse_command_line("wc < input.txt")

        assert len(commands) == 1
        assert commands[0].command == "wc"
        assert commands[0].type == CommandType.REDIRECT_IN
        assert commands[0].target == "input.txt"

    def test_parse_and_operator(self, parser):
        """Test parsing AND operator."""
        commands = parser.parse_command_line("mkdir test && cd test")

        assert len(commands) == 2
        assert commands[0].command == "mkdir"
        assert commands[0].args == ["test"]
        assert commands[0].type == CommandType.AND
        assert commands[1].command == "cd"
        assert commands[1].args == ["test"]

    def test_parse_or_operator(self, parser):
        """Test parsing OR operator."""
        commands = parser.parse_command_line("ls /nonexistent || echo failed")

        assert len(commands) == 2
        assert commands[0].command == "ls"
        assert commands[0].args == ["/nonexistent"]
        assert commands[0].type == CommandType.OR
        assert commands[1].command == "echo"
        assert commands[1].args == ["failed"]

    def test_parse_semicolon_separator(self, parser):
        """Test parsing semicolon separator."""
        commands = parser.parse_command_line("ls; pwd; whoami")

        assert len(commands) == 3
        assert commands[0].command == "ls"
        assert commands[0].type == CommandType.SEMICOLON
        assert commands[1].command == "pwd"
        assert commands[1].type == CommandType.SEMICOLON
        assert commands[2].command == "whoami"

    def test_parse_complex_pipeline(self, parser):
        """Test parsing complex pipeline with redirection."""
        commands = parser.parse_command_line("ps | grep python | wc -l > count.txt")

        assert len(commands) == 3
        assert commands[0].command == "ps"
        assert commands[0].type == CommandType.PIPE
        assert commands[1].command == "grep"
        assert commands[1].type == CommandType.PIPE
        assert commands[2].command == "wc"
        assert commands[2].args == ["-l"]
        assert commands[2].type == CommandType.REDIRECT_OUT
        assert commands[2].target == "count.txt"

    def test_parse_variable_expansion(self, parser):
        """Test variable expansion in parsing."""
        parser.set_variable("USER", "testuser")
        commands = parser.parse_command_line("echo Hello $USER")

        assert len(commands) == 1
        assert commands[0].command == "echo"
        assert commands[0].args == ["Hello", "testuser"]

    @patch("glob.glob")
    def test_parse_glob_expansion(self, mock_glob, parser):
        """Test glob expansion in parsing."""
        mock_glob.return_value = ["file1.txt", "file2.txt"]
        commands = parser.parse_command_line("ls *.txt")

        assert len(commands) == 1
        assert commands[0].command == "ls"
        assert commands[0].args == ["file1.txt", "file2.txt"]

    @patch("glob.glob")
    def test_parse_glob_no_matches(self, mock_glob, parser):
        """Test glob with no matches."""
        mock_glob.return_value = []
        commands = parser.parse_command_line("ls *.nonexistent")

        assert len(commands) == 1
        assert commands[0].command == "ls"
        assert commands[0].args == ["*.nonexistent"]  # Keep original if no matches

    def test_set_and_get_variable(self, parser):
        """Test setting and getting variables."""
        parser.set_variable("TESTVAR", "testvalue")
        assert parser.get_variable("TESTVAR") == "testvalue"

    def test_update_pwd(self, parser):
        """Test updating PWD."""
        parser.update_pwd("/new/directory")
        assert parser.get_variable("PWD") == "/new/directory"

    def test_set_exit_code(self, parser):
        """Test setting exit code."""
        parser.set_exit_code(42)
        assert parser.get_variable("?") == "42"

    def test_parse_quoted_arguments(self, parser):
        """Test parsing commands with quoted arguments."""
        commands = parser.parse_command_line("echo \"hello world\" 'single quotes'")

        assert len(commands) == 1
        assert commands[0].command == "echo"
        assert commands[0].args == ["hello world", "single quotes"]

    def test_parse_pipe_vs_or(self, parser):
        """Test distinguishing between pipe and OR operators."""
        # Test pipe
        commands = parser.parse_command_line("ps | grep test")
        assert len(commands) == 2
        assert commands[0].type == CommandType.PIPE

        # Test OR
        commands = parser.parse_command_line("false || echo backup")
        assert len(commands) == 2
        assert commands[0].type == CommandType.OR


class TestParserModule:
    """Test module-level parser functions."""

    def test_get_shell_parser_singleton(self):
        """Test that get_shell_parser returns singleton."""
        parser1 = get_shell_parser()
        parser2 = get_shell_parser()

        assert parser1 is parser2

    def test_init_shell_parser(self):
        """Test initializing shell parser."""
        variables = ShellVariables()
        parser = init_shell_parser(variables)

        assert isinstance(parser, ShellParser)
        assert parser.variables is variables

        # Should return same instance
        same_parser = get_shell_parser()
        assert parser is same_parser
