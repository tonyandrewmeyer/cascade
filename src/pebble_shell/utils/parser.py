"""Shell command parser for advanced features like pipes, redirection, and chaining."""

from __future__ import annotations

import dataclasses
import enum
import glob
import os
import re


class CommandType(enum.Enum):
    """Types of shell command operations."""

    SIMPLE = "simple"
    PIPE = "pipe"
    REDIRECT_OUT = "redirect_out"
    REDIRECT_APPEND = "redirect_append"
    REDIRECT_IN = "redirect_in"
    AND = "and"
    OR = "or"
    SEMICOLON = "semicolon"


@dataclasses.dataclass
class ParsedCommand:
    """Represents a parsed shell command."""

    command: str
    args: list[str]
    type: CommandType
    target: str | None = None  # For redirection target or next command.
    next_command: ParsedCommand | None = None


class ShellVariables:
    """Manages shell variables and environment expansion."""

    def __init__(self):
        self.variables = {
            "PWD": "/",
            "USER": "root",
            "HOME": "/root",
            "SHELL": "/bin/cascade",
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        }
        self.last_exit_code = 0

    def set_variable(self, name: str, value: str):
        """Set a shell variable."""
        self.variables[name] = value

    def get_variable(self, name: str) -> str:
        """Get a shell variable."""
        if name == "?":
            return str(self.last_exit_code)
        if name in self.variables:
            return self.variables[name]
        return os.environ.get(name, "")

    def expand_variables(self, text: str) -> str:
        """Expand variables in text ($VAR and ${VAR} syntax)."""
        if "$" not in text:
            return text

        # Handle ${VAR} syntax
        def replace_braced(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return self.get_variable(var_name)

        text = re.sub(r"\$\{([^}]+)\}", replace_braced, text)

        # Handle $VAR syntax (word boundaries)
        def replace_simple(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return self.get_variable(var_name)

        text = re.sub(r"\$([A-Za-z_][A-Za-z0-9_]*)", replace_simple, text)

        return text

    def update_pwd(self, new_pwd: str):
        """Update PWD variable."""
        self.variables["PWD"] = new_pwd


class ShellParser:
    """Parser for shell command lines with advanced features."""

    def __init__(self, variables: ShellVariables | None = None):
        self.variables = variables or ShellVariables()

    def parse_command_line(self, command_line: str) -> list[ParsedCommand]:
        """Parse a command line into a list of commands with operations.

        Args:
            command_line: Raw command line string

        Returns:
            List of ParsedCommand objects
        """
        if not command_line.strip():
            return []

        # Expand variables first
        expanded_line = self.variables.expand_variables(command_line.strip())

        # Split by command separators (;, &&, ||)
        command_groups = self._split_by_separators(expanded_line)

        parsed_commands: list[ParsedCommand] = []
        for group, separator in command_groups:
            # Parse individual command group (may contain pipes and redirections)
            commands = self._parse_command_group(group)
            if commands:
                # Set the separator type for the last command in the group
                if separator and commands:
                    if separator == "&&":
                        commands[-1].type = CommandType.AND
                    elif separator == "||":
                        commands[-1].type = CommandType.OR
                    elif separator == ";":
                        commands[-1].type = CommandType.SEMICOLON

                parsed_commands.extend(commands)

        return parsed_commands

    def _split_by_separators(self, command_line: str) -> list[tuple[str, str | None]]:
        """Split command line by separators (;, &&, ||)."""
        # Simple regex-based splitting (could be improved for quoted strings)
        parts: list[tuple[str, str | None]] = []
        current = ""
        i = 0

        while i < len(command_line):
            char = command_line[i]

            if char == ";":
                parts.append((current.strip(), ";"))
                current = ""
                i += 1
            elif (
                char == "&" and i + 1 < len(command_line) and command_line[i + 1] == "&"
            ):
                parts.append((current.strip(), "&&"))
                current = ""
                i += 2
            elif (
                char == "|" and i + 1 < len(command_line) and command_line[i + 1] == "|"
            ):
                parts.append((current.strip(), "||"))
                current = ""
                i += 2
            else:
                current += char
                i += 1

        if current.strip():
            parts.append((current.strip(), None))

        return parts

    def _parse_command_group(self, group: str) -> list[ParsedCommand]:
        """Parse a command group that may contain pipes and redirections."""
        # Split by pipes first
        pipe_parts = self._split_by_pipes(group)

        commands: list[ParsedCommand] = []
        for i, part in enumerate(pipe_parts):
            # Parse redirections in this part
            cmd, redirect_type, redirect_target = self._parse_redirections(part)

            if not cmd.strip():
                continue

            # Parse the actual command and arguments
            try:
                tokens = self._parse_with_bash_quotes(cmd)
            except ValueError:
                # Handle unclosed quotes gracefully
                tokens = cmd.split()

            if not tokens:
                continue

            # Expand globs in arguments
            expanded_tokens = self._expand_globs(tokens)

            command = expanded_tokens[0]
            args = expanded_tokens[1:]

            # Determine command type
            if i < len(pipe_parts) - 1:
                cmd_type = CommandType.PIPE
            elif redirect_type:
                cmd_type = redirect_type
            else:
                cmd_type = CommandType.SIMPLE

            parsed_cmd = ParsedCommand(
                command=command, args=args, type=cmd_type, target=redirect_target
            )

            commands.append(parsed_cmd)

        # Link pipe commands
        for i in range(len(commands) - 1):
            if commands[i].type == CommandType.PIPE:
                commands[i].next_command = commands[i + 1]

        return commands

    def _split_by_pipes(self, group: str) -> list[str]:
        """Split command group by pipes, avoiding || operators."""
        parts: list[str] = []
        current = ""
        i = 0

        while i < len(group):
            char = group[i]

            if char == "|":
                # Check if it's || (OR operator) vs | (pipe)
                if i + 1 < len(group) and group[i + 1] == "|":
                    # It's ||, don't split here
                    current += char
                    i += 1
                else:
                    # It's a pipe
                    parts.append(current.strip())
                    current = ""
                    i += 1
                    continue

            current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts

    def _parse_redirections(
        self, command: str
    ) -> tuple[str, CommandType | None, str | None]:
        """Parse redirection operators in a command."""
        # Simple redirection parsing
        redirect_patterns = [
            (r"\s*>>\s*([^\s]+)", CommandType.REDIRECT_APPEND),
            (r"\s*>\s*([^\s]+)", CommandType.REDIRECT_OUT),
            (r"\s*<\s*([^\s]+)", CommandType.REDIRECT_IN),
        ]

        for pattern, redirect_type in redirect_patterns:
            match = re.search(pattern, command)
            if match:
                target = match.group(1)
                # Remove the redirection from the command
                cmd = re.sub(pattern, "", command).strip()
                return cmd, redirect_type, target

        return command, None, None

    def _expand_globs(self, tokens: list[str]) -> list[str]:
        """Expand glob patterns in command tokens."""
        # For now, we'll use local glob expansion
        # Remote glob expansion will be handled by individual commands
        # that have access to the Pebble client
        expanded: list[str] = []

        for token in tokens:
            if "*" in token or "?" in token or "[" in token:
                try:
                    # Use glob to expand patterns
                    matches = glob.glob(token)
                    if matches:
                        expanded.extend(sorted(matches))
                    else:
                        # No matches, keep original token
                        expanded.append(token)
                except Exception:
                    # Glob failed, keep original
                    expanded.append(token)
            else:
                expanded.append(token)

        return expanded

    def _parse_with_bash_quotes(self, text: str) -> list[str]:
        """Parse command text with bash-like quote handling.

        Supports:
        - Single quotes: preserve everything literally
        - Double quotes: allow variable expansion, escape sequences
        - Backslash escaping outside quotes
        """
        tokens = []
        current_token = ""
        was_quoted = False
        i = 0

        while i < len(text):
            char = text[i]

            # Skip whitespace between tokens
            if not current_token and not was_quoted and char.isspace():
                i += 1
                continue

            # Handle single quotes - literal, no escaping
            if char == "'":
                if current_token and current_token[-1:] == "\\":
                    # Escaped quote, add literally
                    current_token = current_token[:-1] + "'"
                    i += 1
                    continue

                # Find closing single quote
                was_quoted = True
                i += 1
                while i < len(text) and text[i] != "'":
                    current_token += text[i]
                    i += 1
                if i < len(text):  # Skip closing quote
                    i += 1
                continue

            # Handle double quotes - allow variable expansion
            elif char == '"':
                if current_token and current_token[-1:] == "\\":
                    # Escaped quote, add literally
                    current_token = current_token[:-1] + '"'
                    i += 1
                    continue

                # Find closing double quote, expand variables
                was_quoted = True
                i += 1
                while i < len(text) and text[i] != '"':
                    if text[i] == "\\" and i + 1 < len(text):
                        # Handle escape sequences in double quotes
                        next_char = text[i + 1]
                        if next_char in ['"', "\\", "$", "`", "\n"]:
                            current_token += next_char
                            i += 2
                        else:
                            current_token += text[i]
                            i += 1
                    elif text[i] == "$":
                        # Variable expansion in double quotes
                        i += 1
                        if i < len(text) and text[i] == "{":
                            # ${VAR} syntax
                            i += 1
                            var_name = ""
                            while i < len(text) and text[i] != "}":
                                var_name += text[i]
                                i += 1
                            if i < len(text):  # Skip closing brace
                                i += 1
                            current_token += self.variables.get_variable(var_name)
                        else:
                            # $VAR syntax
                            var_name = ""
                            while i < len(text) and (
                                text[i].isalnum() or text[i] in "_?"
                            ):
                                var_name += text[i]
                                i += 1
                            if var_name:
                                current_token += self.variables.get_variable(var_name)
                            else:
                                current_token += "$"
                        continue
                    else:
                        current_token += text[i]
                        i += 1
                if i < len(text):  # Skip closing quote
                    i += 1
                continue

            # Handle backslash escaping outside quotes
            elif char == "\\" and i + 1 < len(text):
                current_token += text[i + 1]
                i += 2
                continue

            # Handle whitespace - end current token
            elif char.isspace():
                if current_token or was_quoted:
                    tokens.append(current_token)
                    current_token = ""
                    was_quoted = False
                i += 1
                continue

            # Handle variable expansion outside quotes
            elif char == "$":
                i += 1
                if i < len(text) and text[i] == "{":
                    # ${VAR} syntax
                    i += 1
                    var_name = ""
                    while i < len(text) and text[i] != "}":
                        var_name += text[i]
                        i += 1
                    if i < len(text):  # Skip closing brace
                        i += 1
                    var_value = self.variables.get_variable(var_name)
                    current_token += var_value
                    # Mark as was_quoted if expanding to empty to ensure token creation
                    if not var_value:
                        was_quoted = True
                else:
                    # $VAR syntax
                    var_name = ""
                    while i < len(text) and (text[i].isalnum() or text[i] in "_?"):
                        var_name += text[i]
                        i += 1
                    if var_name:
                        var_value = self.variables.get_variable(var_name)
                        current_token += var_value
                        # Mark as was_quoted if expanding to empty to ensure token creation
                        if not var_value:
                            was_quoted = True
                    else:
                        current_token += "$"
                continue

            # Regular character
            else:
                current_token += char
                i += 1

        # Add final token
        if current_token or was_quoted:
            tokens.append(current_token)

        return tokens

    def set_variable(self, name: str, value: str) -> None:
        """Set a shell variable."""
        self.variables.set_variable(name, value)

    def get_variable(self, name: str) -> str:
        """Get a shell variable."""
        return self.variables.get_variable(name)

    def update_pwd(self, new_pwd: str) -> None:
        """Update current working directory."""
        self.variables.update_pwd(new_pwd)

    def set_exit_code(self, code: int) -> None:
        """Set last command exit code."""
        self.variables.last_exit_code = code

    def get_exit_code(self) -> int:
        """Get last command exit code."""
        return self.variables.last_exit_code


# Global parser instance
_shell_parser: ShellParser | None = None


def get_shell_parser() -> ShellParser:
    """Get the global shell parser instance."""
    global _shell_parser
    if _shell_parser is None:
        _shell_parser = ShellParser()
    # Type checker workaround - we know _shell_parser is not None here
    return _shell_parser  # type: ignore[return-value]


def init_shell_parser(variables: ShellVariables | None = None) -> ShellParser:
    """Initialise the global shell parser.

    Args:
        variables: Optional ShellVariables instance

    Returns:
        ShellParser instance
    """
    global _shell_parser
    _shell_parser = ShellParser(variables)
    return _shell_parser
