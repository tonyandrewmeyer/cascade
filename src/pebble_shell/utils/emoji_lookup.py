"""Emoji lookup utilities with graceful degradation.

This module provides emoji search functionality using the emoji library as an
optional dependency. When emoji is not installed, functions raise
EmojiUnavailableError with helpful installation instructions.
"""

from __future__ import annotations


class EmojiUnavailableError(Exception):
    """Raised when emoji functionality is not available."""

    pass


# Try to import emoji
EMOJI_AVAILABLE = False
_emoji = None

try:
    import emoji as _emoji

    EMOJI_AVAILABLE = True
except ImportError:
    pass


INSTALL_INSTRUCTIONS = "Install with: pip install pebble-cascade[emoji]"


def _check_available() -> None:
    """Check if emoji library is available, raise if not."""
    if not EMOJI_AVAILABLE:
        raise EmojiUnavailableError(
            f"Emoji support not available. emoji library is not installed.\n"
            f"{INSTALL_INSTRUCTIONS}"
        )


def search_emoji(query: str, limit: int = 20) -> list[tuple[str, str]]:
    """Search for emojis matching a query.

    Args:
        query: Search term to match against emoji names.
        limit: Maximum number of results to return.

    Returns:
        List of (emoji_char, name) tuples matching the query.

    Raises:
        EmojiUnavailableError: If emoji library is not installed.
    """
    _check_available()
    assert _emoji is not None

    query_lower = query.lower()
    results: list[tuple[str, str]] = []

    for emoji_char, data in _emoji.EMOJI_DATA.items():
        # Search in English name
        if "en" in data:
            name = data["en"]
            # Remove colons from name for matching
            clean_name = name.strip(":").replace("_", " ")
            if query_lower in clean_name.lower():
                results.append((emoji_char, clean_name))
                if len(results) >= limit:
                    break

    return results


def get_emoji_by_name(name: str) -> str | None:
    """Get an emoji by its exact name.

    Args:
        name: The emoji name (with or without colons).

    Returns:
        The emoji character, or None if not found.

    Raises:
        EmojiUnavailableError: If emoji library is not installed.
    """
    _check_available()
    assert _emoji is not None

    # Normalize the name to have colons
    if not name.startswith(":"):
        name = ":" + name
    if not name.endswith(":"):
        name = name + ":"

    # Replace spaces with underscores
    name = name.replace(" ", "_")

    return _emoji.emojize(name, language="en")


def is_emoji_available() -> bool:
    """Check if emoji functionality is available.

    Returns:
        True if emoji library is installed.
    """
    return EMOJI_AVAILABLE
