"""Utility functions for Cascade."""

from .dashboard import SystemDashboard, SystemStats
from .enhanced_completer import EnhancedCompleter
from .executor import CommandOutput, PipelineExecutor
from .formatting import (
    format_bytes,
    format_error,
    format_file_info,
    format_relative_time,
    format_stat_info,
    format_time,
)
from .glob_utils import (
    expand_globs_in_tokens,
    expand_remote_globs,
    expand_remote_globs_recursive,
)
from .history import ShellHistory, get_shell_history, init_shell_history
from .parser import (
    ParsedCommand,
    ShellParser,
    ShellVariables,
    get_shell_parser,
    init_shell_parser,
)
from .pathutils import resolve_path
from .readline_support import ReadlineWrapper, ShellCompleter, setup_readline_support

__all__ = [
    "CommandOutput",
    "EnhancedCompleter",
    "ParsedCommand",
    "PipelineExecutor",
    "ReadlineWrapper",
    "ShellCompleter",
    "ShellHistory",
    "ShellParser",
    "ShellVariables",
    "SystemDashboard",
    "SystemStats",
    "expand_globs_in_tokens",
    "expand_remote_globs",
    "expand_remote_globs_recursive",
    "format_bytes",
    "format_error",
    "format_file_info",
    "format_relative_time",
    "format_stat_info",
    "format_time",
    "get_shell_history",
    "get_shell_parser",
    "init_shell_history",
    "init_shell_parser",
    "resolve_path",
    "setup_readline_support",
]
