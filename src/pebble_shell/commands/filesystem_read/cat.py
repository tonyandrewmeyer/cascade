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
    help = "Display file contents: Usage: cat [-nbETAs] <file> [file2 ...]"
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

        flags_result = parse_flags(
            args,
            {
                "plain": bool,
                "n": bool,
                "number": bool,
                "b": bool,
                "number-nonblank": bool,
                "E": bool,
                "show-ends": bool,
                "T": bool,
                "show-tabs": bool,
                "A": bool,
                "show-all": bool,
                "s": bool,
                "squeeze-blank": bool,
            },
            self.shell,
        )
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
        )
        if file_paths is None:
            return 1

        # Resolve combined flags
        number = flags["n"] or flags["number"]
        number_nonblank = flags["b"] or flags["number-nonblank"]
        show_ends = flags["E"] or flags["show-ends"]
        show_tabs = flags["T"] or flags["show-tabs"]
        show_all = flags["A"] or flags["show-all"]
        squeeze_blank = flags["s"] or flags["squeeze-blank"]
        plain = flags["plain"]

        # -A is equivalent to -ET
        if show_all:
            show_ends = True
            show_tabs = True

        # -b overrides -n
        if number_nonblank:
            number = False

        # Any text-processing flag implies plain mode
        has_text_flags = (
            number or number_nonblank or show_ends or show_tabs or squeeze_blank
        )

        exit_code = 0

        # Process files with progress tracking
        with create_file_progress() as progress:
            task = progress.add_task("Reading files...", total=len(file_paths))

            for file_path in file_paths:
                # Read file content safely
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    exit_code = 1
                    progress.advance(task)
                    continue

                # Print file header for multiple files
                header = format_file_header(file_path, len(file_paths))
                if header:
                    self.shell.console.print(header)

                # Display content based on file type and flags
                if has_text_flags:
                    self._display_with_flags(
                        content,
                        number=number,
                        number_nonblank=number_nonblank,
                        show_ends=show_ends,
                        show_tabs=show_tabs,
                        squeeze_blank=squeeze_blank,
                    )
                else:
                    self._display_content(content, file_path, plain)
                progress.advance(task)

        return exit_code

    def _display_with_flags(
        self,
        content: str,
        *,
        number: bool = False,
        number_nonblank: bool = False,
        show_ends: bool = False,
        show_tabs: bool = False,
        squeeze_blank: bool = False,
    ) -> None:
        """Display file content with text-processing flags (plain mode)."""
        lines = content.split("\n")
        # If content ends with newline, split produces a trailing empty string
        # which represents the newline at the end, not an extra line
        if content.endswith("\n") and lines and lines[-1] == "":
            lines = lines[:-1]
            trailing_newline = True
        else:
            trailing_newline = False

        line_number = 0
        prev_blank = False
        output_lines: list[str] = []

        for line in lines:
            is_blank = line == ""

            # Squeeze blank lines
            if squeeze_blank and is_blank and prev_blank:
                continue
            prev_blank = is_blank

            # Apply tab substitution
            if show_tabs:
                line = line.replace("\t", "^I")

            # Apply line endings
            if show_ends:
                line = line + "$"

            # Apply line numbering
            if number:
                line_number += 1
                line = f"{line_number:6d}\t{line}"
            elif number_nonblank:
                if not is_blank:
                    line_number += 1
                    line = f"{line_number:6d}\t{line}"

            output_lines.append(line)

        result = "\n".join(output_lines)
        if trailing_newline:
            result += "\n"
        self.shell.console.print(result, end="", highlight=False)

    def _display_content(self, content: str, file_path: str, plain: bool) -> None:
        """Display file content with appropriate formatting."""
        if plain:
            self.shell.console.print(content, end="", highlight=False)
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
