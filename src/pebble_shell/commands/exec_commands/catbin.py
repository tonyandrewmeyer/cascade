"""Display the source code of a command in the path.

catbin foo is basically cat "$(which foo)" - useful for seeing the source code
of scripts in your path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Union

import ops
from rich.syntax import Syntax

from ...utils.command_helpers import parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class CatbinCommand(Command):
    """Display the source code of a command in the path."""

    name = "catbin"
    help = "Display the source code of a command in the path"
    category = "Remote Execution"

    # Map file extensions to syntax lexers
    CODE_EXTENSIONS: ClassVar[dict[str, str]] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".rb": "ruby",
        ".pl": "perl",
        ".php": "php",
        ".go": "go",
        ".rs": "rust",
    }

    def show_help(self):
        """Show command help."""
        help_text = """Display the source code of a command in the path.

Usage: catbin [OPTIONS] COMMAND

Options:
    -h, --help      Show this help message
    -p, --plain     Display without syntax highlighting
    -n, --no-lines  Don't show line numbers

Arguments:
    COMMAND         Name of command to display source for

This runs 'which COMMAND' on the remote system to find the path,
then displays the file contents with syntax highlighting.

Examples:
    catbin foo           # Show source of 'foo' script
    catbin -p foo        # Show without syntax highlighting
    catbin --plain foo   # Same as above
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the catbin command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "p": bool,
                "plain": bool,
                "n": bool,
                "no-lines": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not positional_args:
            self.console.print("[red]catbin: missing command argument[/red]")
            self.console.print("Usage: catbin <command>")
            return 1

        command_name = positional_args[0]
        plain = flags["p"] or flags["plain"]
        no_lines = flags["n"] or flags["no-lines"]

        # Run 'which' on the remote system to get the path
        try:
            process = client.exec(["which", command_name])
            stdout, stderr = process.wait_output()
        except ops.pebble.ExecError as e:
            self.console.print(f"[red]catbin: 'which' command failed: {e}[/red]")
            return 1
        except ops.pebble.APIError as e:
            self.console.print(
                "[red]catbin: 'which' command not available on remote system[/red]"
            )
            self.console.print(f"[dim]Error: {e}[/dim]")
            return 1

        if not stdout or not stdout.strip():
            self.console.print(f"[red]catbin: {command_name}: not found in PATH[/red]")
            return 1

        bin_path = stdout.strip()

        # Read the file at that path
        content = safe_read_file(client, bin_path, self.shell)
        if content is None:
            return 1

        # Display the content
        self._display_content(content, bin_path, plain, no_lines)
        return 0

    def _display_content(
        self, content: str, file_path: str, plain: bool, no_lines: bool
    ) -> None:
        """Display file content with appropriate formatting."""
        if plain:
            self.console.print(content, end="")
            if content and not content.endswith("\n"):
                self.console.print()
            return

        # Determine lexer from file extension or shebang
        lexer = self._detect_lexer(content, file_path)

        if lexer:
            syntax = Syntax(
                content,
                lexer,
                theme="monokai",
                line_numbers=not no_lines,
                word_wrap=False,
            )
            self.console.print(syntax)
        else:
            self.console.print(content, end="")
            if content and not content.endswith("\n"):
                self.console.print()

    def _detect_lexer(self, content: str, file_path: str) -> str | None:
        """Detect the appropriate syntax lexer for a file."""
        # Check file extension first
        for ext, lexer in self.CODE_EXTENSIONS.items():
            if file_path.endswith(ext):
                return lexer

        # Check shebang
        if content.startswith("#!"):
            first_line = content.split("\n", 1)[0].lower()
            if "python" in first_line:
                return "python"
            if "bash" in first_line or "/sh" in first_line:
                return "bash"
            if "zsh" in first_line:
                return "zsh"
            if "perl" in first_line:
                return "perl"
            if "ruby" in first_line:
                return "ruby"
            if "node" in first_line or "javascript" in first_line:
                return "javascript"
            if "php" in first_line:
                return "php"

        return None
