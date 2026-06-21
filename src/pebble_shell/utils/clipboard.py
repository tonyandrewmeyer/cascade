"""Clipboard utilities with graceful degradation.

This module provides clipboard access using pyperclip as an optional dependency.
When pyperclip is not installed, functions raise ClipboardUnavailableError with
helpful installation instructions.
"""

from __future__ import annotations


class ClipboardUnavailableError(Exception):
    """Raised when clipboard functionality is not available."""

    pass


class ClipboardAccessError(Exception):
    """Raised when clipboard access fails."""

    pass


# Try to import pyperclip
CLIPBOARD_AVAILABLE = False
_pyperclip = None

try:
    import pyperclip as _pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    pass


INSTALL_INSTRUCTIONS = "Install with: pip install pebble-cascade[clipboard]"


def _check_available() -> None:
    """Check if clipboard is available, raise if not."""
    if not CLIPBOARD_AVAILABLE:
        raise ClipboardUnavailableError(
            f"Clipboard support not available. pyperclip is not installed.\n"
            f"{INSTALL_INSTRUCTIONS}"
        )


def copy_to_clipboard(text: str) -> None:
    """Copy text to the clipboard.

    Args:
        text: The text to copy to the clipboard.

    Raises:
        ClipboardUnavailableError: If pyperclip is not installed.
        ClipboardAccessError: If clipboard access fails.
    """
    _check_available()
    try:
        assert _pyperclip is not None
        _pyperclip.copy(text)
    except Exception as e:
        # pyperclip can raise various exceptions depending on the platform
        # (e.g., PyperclipException on Linux without xclip/xsel)
        raise ClipboardAccessError(
            f"Failed to access clipboard: {e}\n"
            "On Linux, ensure xclip or xsel is installed."
        ) from e


def paste_from_clipboard() -> str:
    """Get text from the clipboard.

    Returns:
        The current clipboard contents as a string.

    Raises:
        ClipboardUnavailableError: If pyperclip is not installed.
        ClipboardAccessError: If clipboard access fails.
    """
    _check_available()
    try:
        assert _pyperclip is not None
        return _pyperclip.paste()
    except Exception as e:
        raise ClipboardAccessError(
            f"Failed to access clipboard: {e}\n"
            "On Linux, ensure xclip or xsel is installed."
        ) from e


def is_clipboard_available() -> bool:
    """Check if clipboard functionality is available.

    Returns:
        True if pyperclip is installed and clipboard can be accessed.
    """
    return CLIPBOARD_AVAILABLE
