"""Standardised error handling utilities for Pebble operations.

This module provides common error handling patterns and utilities that are
frequently used across command modules when working with Pebble client operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

import ops
from rich.panel import Panel

if TYPE_CHECKING:
    from collections.abc import Callable

    from rich.console import Console

T = TypeVar("T")


def handle_pebble_path_error(
    console: Console, operation: str, path: str, error: ops.pebble.PathError
) -> None:
    """Handle Pebble PathError with standardized formatting.

    Args:
        console: Rich console for output
        operation: Description of the operation that failed (e.g., "read file")
        path: File path that caused the error
        error: The PathError that occurred
    """
    error_message = f"Failed to {operation}: {path}"
    detail = str(error)

    content = f"[red]{error_message}[/red]\n[yellow]{detail}[/yellow]"
    panel = Panel(
        content,
        title="[bold red]Error[/bold red]",
        border_style="red",
        expand=False,
    )
    console.print(panel)


def handle_pebble_api_error(
    console: Console, operation: str, error: ops.pebble.APIError
) -> None:
    """Handle Pebble APIError with standardized formatting.

    Args:
        console: Rich console for output
        operation: Description of the operation that failed
        error: The APIError that occurred
    """
    error_message = f"API error during {operation}"
    detail = str(error)

    content = f"[red]{error_message}[/red]\n[yellow]{detail}[/yellow]"
    panel = Panel(
        content,
        title="[bold red]API Error[/bold red]",
        border_style="red",
        expand=False,
    )
    console.print(panel)


def handle_generic_pebble_error(
    console: Console, operation: str, error: Exception, context: str = ""
) -> None:
    """Handle generic Pebble-related errors with standardized formatting.

    Args:
        console: Rich console for output
        operation: Description of the operation that failed
        error: The exception that occurred
        context: Optional additional context information
    """
    error_message = f"Error during {operation}"
    if context:
        error_message += f" ({context})"

    detail = f"{error.__class__.__name__}: {error}"

    content = f"[red]{error_message}[/red]\n[yellow]{detail}[/yellow]"
    panel = Panel(
        content,
        title="[bold red]Error[/bold red]",
        border_style="red",
        expand=False,
    )
    console.print(panel)


def safe_pebble_operation(
    console: Console, operation: Callable[[], T], operation_name: str, context: str = ""
) -> T | None:
    """Safely execute a Pebble operation with standardized error handling.

    Args:
        console: Rich console for error output
        operation: Function to execute that may raise Pebble exceptions
        operation_name: Human-readable description of the operation
        context: Optional additional context for error messages

    Returns:
        Result of the operation if successful, None if it failed
    """
    try:
        return operation()
    except ops.pebble.PathError as e:
        handle_pebble_path_error(console, operation_name, context or "unknown path", e)
        return None
    except ops.pebble.APIError as e:
        handle_pebble_api_error(console, operation_name, e)
        return None
    except Exception as e:
        handle_generic_pebble_error(console, operation_name, e, context)
        return None


def show_file_not_found_error(console: Console, path: str, command: str = "") -> None:
    """Show a standardized file not found error message.

    Args:
        console: Rich console for output
        path: Path that was not found
        command: Optional command name for context
    """
    prefix = f"{command}: " if command else ""
    error_message = f"{prefix}No such file or directory: {path}"

    console.print(f"[red]{error_message}[/red]")


def show_permission_error(
    console: Console, path: str, operation: str, command: str = ""
) -> None:
    """Show a standardized permission error message.

    Args:
        console: Rich console for output
        path: Path that caused the permission error
        operation: Operation that was attempted (e.g., "read", "write")
        command: Optional command name for context
    """
    prefix = f"{command}: " if command else ""
    error_message = f"{prefix}Permission denied: cannot {operation} {path}"

    console.print(f"[red]{error_message}[/red]")


def validate_file_exists(
    console: Console, client: Any, path: str, command: str = ""
) -> bool:
    """Validate that a file exists with standardized error handling.

    Args:
        console: Rich console for error output
        client: Pebble client instance
        path: Path to check
        command: Optional command name for context

    Returns:
        True if file exists, False otherwise (with error message displayed)
    """
    try:
        client.list_files(path, itself=True)
        return True
    except ops.pebble.PathError:
        show_file_not_found_error(console, path, command)
        return False
    except ops.pebble.APIError as e:
        handle_pebble_api_error(console, f"check file existence for {path}", e)
        return False


def show_usage_error(
    console: Console, command: str, usage: str, message: str = ""
) -> int:
    """Show a standardized usage error with command usage information.

    Args:
        console: Rich console for output
        command: Command name
        usage: Usage string for the command
        message: Optional additional error message

    Returns:
        Exit code 1
    """
    if message:
        console.print(f"[red]{command}: {message}[/red]")

    console.print(f"Usage: {usage}")
    return 1


def with_error_context(operation_name: str, context: str = ""):
    """Decorator to add standardized error handling to command methods.

    Args:
        operation_name: Human-readable name of the operation
        context: Optional additional context information

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        def wrapper(self, *args, **kwargs) -> T | None:
            try:
                return func(self, *args, **kwargs)
            except ops.pebble.PathError as e:
                handle_pebble_path_error(
                    self.console, operation_name, context or "unknown path", e
                )
                return None
            except ops.pebble.APIError as e:
                handle_pebble_api_error(self.console, operation_name, e)
                return None
            except Exception as e:
                handle_generic_pebble_error(self.console, operation_name, e, context)
                return None

        return wrapper

    return decorator
