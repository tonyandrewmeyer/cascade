"""Unit tests for bash-like quote handling in the parser."""

from pebble_shell.utils.parser import ShellParser, ShellVariables


class TestQuoteHandling:
    """Test bash-like quote handling functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.variables = ShellVariables()
        self.variables.set_variable("TEST_VAR", "test_value")
        self.variables.set_variable("HOME", "/home/user")
        self.parser = ShellParser(self.variables)

    def test_single_quotes_literal(self):
        """Test that single quotes preserve everything literally."""
        result = self.parser._parse_with_bash_quotes("'hello world'")
        assert result == ["hello world"]

    def test_single_quotes_no_variable_expansion(self):
        """Test that variables are not expanded inside single quotes."""
        result = self.parser._parse_with_bash_quotes("'$TEST_VAR'")
        assert result == ["$TEST_VAR"]

    def test_double_quotes_preserve_spaces(self):
        """Test that double quotes preserve spaces."""
        result = self.parser._parse_with_bash_quotes('"hello world"')
        assert result == ["hello world"]

    def test_double_quotes_variable_expansion(self):
        """Test that variables are expanded inside double quotes."""
        result = self.parser._parse_with_bash_quotes('"$TEST_VAR"')
        assert result == ["test_value"]

    def test_double_quotes_braced_variable_expansion(self):
        """Test that ${VAR} variables are expanded inside double quotes."""
        result = self.parser._parse_with_bash_quotes('"${TEST_VAR}"')
        assert result == ["test_value"]

    def test_double_quotes_escape_sequences(self):
        """Test escape sequences inside double quotes."""
        result = self.parser._parse_with_bash_quotes(r'"hello \"world\""')
        assert result == ['hello "world"']

    def test_backslash_escaping_outside_quotes(self):
        """Test backslash escaping outside quotes."""
        result = self.parser._parse_with_bash_quotes(r"hello\ world")
        assert result == ["hello world"]

    def test_mixed_quoting(self):
        """Test mixing single and double quotes."""
        result = self.parser._parse_with_bash_quotes("'hello' \"world\"")
        assert result == ["hello", "world"]

    def test_variable_expansion_outside_quotes(self):
        """Test variable expansion works outside quotes."""
        result = self.parser._parse_with_bash_quotes("$TEST_VAR")
        assert result == ["test_value"]

    def test_braced_variable_expansion_outside_quotes(self):
        """Test ${VAR} variable expansion works outside quotes."""
        result = self.parser._parse_with_bash_quotes("${HOME}/file")
        assert result == ["/home/user/file"]

    def test_unknown_variable_expansion(self):
        """Test unknown variables expand to empty string."""
        result = self.parser._parse_with_bash_quotes("$UNKNOWN_VAR")
        assert result == [""]

    def test_special_variable_expansion(self):
        """Test special variables like $? expand correctly."""
        self.variables.last_exit_code = 42
        result = self.parser._parse_with_bash_quotes("$?")
        assert result == ["42"]

    def test_unclosed_single_quote(self):
        """Test handling of unclosed single quotes."""
        result = self.parser._parse_with_bash_quotes("'hello world")
        assert result == ["hello world"]  # Should consume to end

    def test_unclosed_double_quote(self):
        """Test handling of unclosed double quotes."""
        result = self.parser._parse_with_bash_quotes('"hello world')
        assert result == ["hello world"]  # Should consume to end

    def test_empty_quotes(self):
        """Test empty quoted strings."""
        result = self.parser._parse_with_bash_quotes('""')
        assert result == [""]

        result = self.parser._parse_with_bash_quotes("''")
        assert result == [""]

    def test_complex_quoting_scenario(self):
        """Test a complex scenario with mixed quoting and variables."""
        cmd = "\"$TEST_VAR\" 'literal $TEST_VAR' $HOME/file"
        result = self.parser._parse_with_bash_quotes(cmd)
        assert result == ["test_value", "literal $TEST_VAR", "/home/user/file"]

    def test_escaped_dollar_in_double_quotes(self):
        """Test escaped dollar sign in double quotes."""
        result = self.parser._parse_with_bash_quotes(r'"price is \$5"')
        assert result == ["price is $5"]

    def test_whitespace_handling(self):
        """Test proper whitespace handling with quotes."""
        result = self.parser._parse_with_bash_quotes('  "hello"   "world"  ')
        assert result == ["hello", "world"]

    def test_concatenated_quotes(self):
        """Test concatenated quoted strings."""
        result = self.parser._parse_with_bash_quotes('hello"world"test')
        assert result == ["helloworldtest"]

    def test_dollar_without_variable_name(self):
        """Test bare dollar sign handling."""
        result = self.parser._parse_with_bash_quotes('"$"')
        assert result == ["$"]  # Should remain as literal $

    def test_nested_brace_in_variable(self):
        """Test variable expansion with nested content."""
        self.variables.set_variable("PATH", "/bin:/usr/bin")
        result = self.parser._parse_with_bash_quotes('"${PATH}"')
        assert result == ["/bin:/usr/bin"]
