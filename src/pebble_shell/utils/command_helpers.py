"""Command helper utilities for eliminating common patterns across Cascade commands."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, cast

import ops
from rich import box
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

if TYPE_CHECKING:
    import shimmer

    from .. import PebbleShell

    PebbleClient = ops.pebble.Client | shimmer.PebbleCliClient

from . import expand_globs_in_tokens, resolve_path


def handle_help_flag(command_instance, args: list[str]) -> bool:
    """Handle -h/--help flags. Returns True if help was shown."""
    if "-h" in args or "--help" in args:
        command_instance.show_help()
        return True
    return False


def validate_min_args(
    shell: PebbleShell, args: list[str], min_count: int, usage_msg: str = ""
) -> bool:
    """Validate minimum argument count and show usage if needed."""
    if len(args) < min_count:
        from .theme import get_theme

        theme = get_theme()
        if usage_msg:
            shell.console.print(
                f"{theme.highlight_text('Usage:')} {theme.primary_text(usage_msg)}"
            )
        else:
            shell.console.print(
                theme.error_text(f"Error: At least {min_count} argument(s) required")
            )
        return False
    return True


def parse_flags(
    args: list[str],
    valid_flags: dict[str, type],
    shell: PebbleShell | None = None,
) -> tuple[dict[str, Any], list[str]] | None:
    """Parse command flags and return (flags_dict, remaining_args).

    Args:
        args: Command line arguments
        valid_flags: Dict mapping flag names to their types (bool, str, int)
        shell: Shell instance for error reporting

    Returns:
        Tuple of (flags_dict, remaining_args) or None if parsing failed

    Example:
        flags, files = parse_flags(args, {"l": bool, "h": bool}, shell)
        if flags is None:
            return 1
    """
    flags = {}
    remaining = []

    # Initialize flags with default values
    for flag_name, flag_type in valid_flags.items():
        if flag_type is bool:
            flags[flag_name] = False
        elif flag_type is int:
            flags[flag_name] = None
        else:
            flags[flag_name] = None

    i = 0
    while i < len(args):
        arg = args[i]

        if arg.startswith("-") and len(arg) > 1:
            # Handle combined flags like "-la" or single flags like "-l"
            flag_chars = arg[1:]  # Remove the dash

            for flag_char in flag_chars:
                if flag_char in valid_flags:
                    flag_type = valid_flags[flag_char]

                    if flag_type is bool:
                        flags[flag_char] = True
                    elif flag_type in (str, int):
                        # For non-bool flags, they need their own argument
                        if len(flag_chars) > 1:
                            # Can't combine non-bool flags with others
                            if shell:
                                from .theme import get_theme

                                theme = get_theme()
                                shell.console.print(
                                    theme.error_text(
                                        f"Error: Flag -{flag_char} cannot be combined with other flags"
                                    )
                                )
                            return None

                        if i + 1 >= len(args):
                            if shell:
                                from .theme import get_theme

                                theme = get_theme()
                                shell.console.print(
                                    theme.error_text(
                                        f"Error: Flag -{flag_char} requires an argument"
                                    )
                                )
                            return None

                        value = args[i + 1]
                        if flag_type is int:
                            try:
                                flags[flag_char] = int(value)
                            except ValueError:
                                if shell:
                                    from .theme import get_theme

                                    theme = get_theme()
                                    shell.console.print(
                                        theme.error_text(
                                            f"Error: Flag -{flag_char} requires an integer argument"
                                        )
                                    )
                                return None
                        else:
                            flags[flag_char] = value
                        i += 1  # Skip the flag argument
                        break  # Only one non-bool flag allowed
                else:
                    if shell:
                        from .theme import get_theme

                        theme = get_theme()
                        shell.console.print(
                            theme.error_text(f"Error: Invalid option -{flag_char}")
                        )
                    return None
        else:
            remaining.append(arg)

        i += 1

    return flags, remaining


def process_file_arguments(
    shell: PebbleShell,
    client: PebbleClient,
    args: list[str],
    allow_globs: bool = True,
    min_files: int = 1,
    max_files: int | None = None,
) -> list[str] | None:
    """Process file arguments with path resolution and optional glob expansion.

    Args:
        shell: Shell instance
        client: Pebble client
        args: File arguments to process
        allow_globs: Whether to expand glob patterns
        min_files: Minimum number of files required
        max_files: Maximum number of files allowed (None for unlimited)

    Returns:
        List of resolved file paths or None if validation failed
    """
    if allow_globs:
        expanded_args = expand_globs_in_tokens(client, args, shell.current_directory)
        if not expanded_args:
            shell.console.print("Error: No files match the pattern")
            return None
        processed = expanded_args
    else:
        processed = args

    if len(processed) < min_files:
        shell.console.print(f"Error: At least {min_files} file(s) required")
        return None

    if max_files is not None and len(processed) > max_files:
        shell.console.print(f"Error: At most {max_files} file(s) allowed")
        return None

    return [resolve_path(shell.current_directory, f, shell.home_dir) for f in processed]


def safe_read_file(
    client: PebbleClient,
    file_path: str,
    shell: PebbleShell | None = None,
) -> str | None:
    """Safely read a file with error handling.

    Args:
        client: Pebble client
        file_path: Path to file to read
        shell: Shell instance for error reporting

    Returns:
        File content as string or None if reading failed
    """
    try:
        with client.pull(file_path) as file:
            content = file.read()
            assert isinstance(content, str)
            return content
    except ops.pebble.PathError as e:
        if shell:
            shell.console.print(f"Error reading file {file_path}: {e}")
        return None


def safe_read_file_lines(
    client: PebbleClient,
    file_path: str,
    shell: PebbleShell | None = None,
) -> list[str] | None:
    """Safely read a file and return its lines.

    Args:
        client: Pebble client
        file_path: Path to file to read
        shell: Shell instance for error reporting

    Returns:
        List of file lines or None if reading failed
    """
    try:
        with client.pull(file_path) as file:
            content = file.read()
            if isinstance(content, bytes):
                try:
                    content = content.decode("utf-8")
                except UnicodeDecodeError:
                    content = cast("bytes", content).decode("utf-8", errors="replace")
            # content is now str
            return content.splitlines()
    except ops.pebble.PathError as e:
        if shell:
            shell.console.print(f"Error reading file {file_path}: {e}")
        return None


def create_standard_table() -> Table:
    """Create a standard Rich table with common styling."""
    return Table(
        show_header=True,
        header_style="bold magenta",
        box=None,
        expand=False,
    )


def create_system_table() -> Table:
    """Create a system table with enhanced styling."""
    return Table(
        show_header=True,
        header_style="bold magenta",
        box=box.SIMPLE_HEAVY,
        expand=False,
        border_style="bright_blue",
    )


def create_file_progress() -> Progress:
    """Create a standard progress bar for file operations."""
    return Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("{task.description}"),
        transient=True,
    )


# Standard column configurations for common table types
COLUMN_CONFIGS = {
    "name": ("Name", "bold", False, "left"),
    "filename": ("Filename", "bold", False, "left"),
    "size": ("Size", "yellow", True, "right"),
    "modified": ("Modified", "white", True, "left"),
    "time": ("Time", "white", True, "left"),
    "pid": ("PID", "cyan", True, "left"),
    "ppid": ("PPID", "cyan", True, "left"),
    "user": ("User", "green", True, "left"),
    "uid": ("UID", "green", True, "left"),
    "gid": ("GID", "green", True, "left"),
    "command": ("Command", "white", False, "left"),
    "cpu": ("CPU%", "yellow", True, "right"),
    "mem": ("MEM%", "yellow", True, "right"),
    "vsz": ("VSZ", "cyan", True, "right"),
    "rss": ("RSS", "cyan", True, "right"),
    "tty": ("TTY", "white", True, "left"),
    "stat": ("STAT", "magenta", True, "left"),
    "start": ("START", "white", True, "left"),
    "mode": ("Mode", "cyan", True, "left"),
    "permissions": ("Permissions", "cyan", True, "left"),
    "owner": ("Owner", "green", True, "left"),
    "group": ("Group", "green", True, "left"),
    "interface": ("Interface", "cyan", True, "left"),
    "address": ("Address", "white", True, "left"),
    "destination": ("Destination", "white", True, "left"),
    "gateway": ("Gateway", "white", True, "left"),
    "flags": ("Flags", "magenta", True, "left"),
    "metric": ("Metric", "yellow", True, "right"),
    "state": ("State", "magenta", True, "left"),
    "local": ("Local Address", "white", True, "left"),
    "foreign": ("Foreign Address", "white", True, "left"),
    "proto": ("Proto", "cyan", True, "left"),
    "recv": ("Recv-Q", "yellow", True, "right"),
    "send": ("Send-Q", "yellow", True, "right"),
    "value": ("Value", "white", False, "left"),
    "field": ("Field", "cyan", True, "left"),
    "path": ("Path", "white", False, "left"),
    "type": ("Type", "magenta", True, "left"),
    "device": ("Device", "cyan", True, "left"),
    "mountpoint": ("Mountpoint", "white", False, "left"),
    "filesystem": ("Filesystem", "white", False, "left"),
    "usage": ("Usage", "yellow", True, "right"),
    "used": ("Used", "yellow", True, "right"),
    "available": ("Available", "green", True, "right"),
    "total": ("Total", "cyan", True, "right"),
}


def add_standard_columns(table: Table, column_types: list[str]) -> None:
    """Add standard columns to a table based on type names.

    Args:
        table: Rich Table instance
        column_types: List of column type names from COLUMN_CONFIGS

    Example:
        table = create_standard_table()
        add_standard_columns(table, ["pid", "user", "command"])
    """
    for col_type in column_types:
        if col_type in COLUMN_CONFIGS:
            name, style, no_wrap, justify = COLUMN_CONFIGS[col_type]
            table.add_column(name, style=style, no_wrap=no_wrap, justify=justify)
        else:
            # Fallback for unknown column types
            table.add_column(col_type.title(), style="white", no_wrap=True)


def check_file_exists(
    client: PebbleClient, file_path: str, shell: PebbleShell | None = None
) -> bool:
    """Check if a file exists using the client.

    Args:
        client: Pebble client
        file_path: Path to check
        shell: Shell instance for error reporting

    Returns:
        True if file exists, False otherwise
    """
    try:
        # Get directory and filename
        dir_path = os.path.dirname(file_path) or "."
        file_name = os.path.basename(file_path)

        files = client.list_files(dir_path)
        return any(f.name == file_name for f in files)
    except (ops.pebble.PathError, ops.pebble.APIError) as e:
        if shell:
            shell.console.print(f"Error checking file {file_path}: {e}")
        return False


def find_files_by_pattern(
    client: PebbleClient,
    directory: str,
    pattern: str,
    shell: PebbleShell | None = None,
) -> list[str]:
    """Find files matching a pattern in a directory.

    Args:
        client: Pebble client
        directory: Directory to search
        pattern: Filename pattern to match
        shell: Shell instance for error reporting

    Returns:
        List of matching file paths
    """
    import fnmatch

    try:
        files = client.list_files(directory)
        return [
            os.path.join(directory, file_info.name)
            for file_info in files
            if fnmatch.fnmatch(file_info.name, pattern)
        ]
    except (ops.pebble.PathError, ops.pebble.APIError) as e:
        if shell:
            shell.console.print(f"Error listing files in {directory}: {e}")
        return []


def parse_lines_argument(
    args: list[str], default_lines: int = 10
) -> tuple[int, list[str]]:
    """Parse a numeric lines argument from command args.

    Args:
        args: Command arguments
        default_lines: Default number of lines if none specified

    Returns:
        Tuple of (lines_count, remaining_args)

    Example:
        lines, files = parse_lines_argument(["10", "file.txt"])
        # lines = 10, files = ["file.txt"]
    """
    lines = default_lines
    remaining_args = []

    for arg in args:
        if arg.isdigit():
            lines = int(arg)
        else:
            remaining_args.append(arg)

    return lines, remaining_args


def format_file_header(file_path: str, file_count: int) -> str | None:
    """Format a file header for multi-file operations.

    Args:
        file_path: Path to the file
        file_count: Total number of files being processed

    Returns:
        Formatted header string or None if only one file
    """
    if file_count > 1:
        return f"==> {file_path} <=="
    return None
