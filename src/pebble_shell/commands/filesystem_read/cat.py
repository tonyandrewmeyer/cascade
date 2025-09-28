"""Cat command for Cascade."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    import ops
    import shimmer

from rich.markdown import Markdown
from rich.syntax import Syntax

from ...utils.command_helpers import (
    create_file_progress,
    format_file_header,
    handle_help_flag,
    parse_flags,
    process_file_arguments,
    safe_read_file,
    validate_min_args,
)
from .._base import Command


class CatCommand(Command):
    """Display file contents."""

    name = "cat"
    help = "Display file contents: Usage: cat <file>"
    category = "Filesystem Commands"

    CODE_EXTENSIONS: ClassVar[dict[str, str]] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".sh": "bash",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".md": "markdown",
        ".html": "html",
        ".css": "css",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".pl": "perl",
        ".php": "php",
        ".xml": "xml",
    }

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute cat command."""
        if handle_help_flag(self, args):
            return 0

        flags_result = parse_flags(args, {"plain": bool}, self.shell)
        if flags_result is None:
            return 1
        flags, remaining_args = flags_result

        if not validate_min_args(self.shell, remaining_args, 1, "cat <file>"):
            return 1

        file_paths = process_file_arguments(
            self.shell,
            client,
            remaining_args,
            allow_globs=True,
            min_files=1,
            max_files=1,
        )
        if file_paths is None:
            return 1

        # Process files with progress tracking
        with create_file_progress() as progress:
            task = progress.add_task("Reading files...", total=len(file_paths))

            for file_path in file_paths:
                # Read file content safely
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                # Print file header for multiple files
                header = format_file_header(file_path, len(file_paths))
                if header:
                    self.shell.console.print(header)

                # Display content based on file type and flags
                self._display_content(content, file_path, flags["plain"])
                progress.advance(task)

        return 0

    def _display_content(self, content: str, file_path: str, plain: bool) -> None:
        """Display file content with appropriate formatting."""
        if plain:
            self.shell.console.print(content, end="")
            return

        # Determine file extension for syntax highlighting
        ext: str | None = None
        for known_ext in self.CODE_EXTENSIONS:
            if file_path.endswith(known_ext):
                ext = known_ext
                break

        # Apply appropriate formatting
        if ext == ".md":
            md = Markdown(content, code_theme="monokai", justify="left")
            self.shell.console.print(md)
        elif ext == ".json":
            self.shell.console.print_json(content)
        elif ext and ext in self.CODE_EXTENSIONS:
            lexer = self.CODE_EXTENSIONS[ext]
            syntax = Syntax(
                content,
                lexer,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
            )
            self.shell.console.print(syntax)
        else:
            self.shell.console.print(content, end="")

        # Add newline between files if content doesn't end with one
        if content and not content.endswith("\n") and (plain or not ext):
            self.shell.console.print()
