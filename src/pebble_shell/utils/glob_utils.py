"""Remote glob expansion utilities for Pebble filesystem."""

from __future__ import annotations

import fnmatch
import os
from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    import shimmer


def expand_remote_globs(
    client: ops.pebble.Client | shimmer.PebbleCliClient,
    pattern: str,
    base_path: str = "/",
) -> list[str]:
    """Expand glob patterns against the remote filesystem.

    Args:
        client: Pebble client for remote filesystem access
        pattern: Glob pattern to expand (e.g., "*.txt", "file*", "dir/*")
        base_path: Base directory to search from (default: "/")

    Returns:
        List of matching file paths
    """
    if not pattern or pattern == "." or pattern == "..":
        return [pattern]

    # Handle absolute paths:
    if pattern.startswith("/"):
        base_path = "/"
        pattern = pattern[1:]

    # Split pattern into directory and filename parts:
    dir_parts = pattern.split("/")
    filename_pattern = dir_parts[-1]
    dir_path = "/".join(dir_parts[:-1]) if len(dir_parts) > 1 else ""

    # Resolve the directory path:
    search_dir = os.path.join(base_path, dir_path).replace("//", "/")
    if search_dir.endswith("/") and len(search_dir) > 1:
        search_dir = search_dir[:-1]

    try:
        files = client.list_files(search_dir)
    except ops.pebble.PathError:
        return [pattern]

    matches: list[str] = []
    for file_info in files:
        filename = file_info.name

        if filename in (".", ".."):
            continue

        # Check if filename matches the pattern:
        if fnmatch.fnmatch(filename, filename_pattern):
            full_path = f"{dir_path}/{filename}" if dir_path else filename

            # Handle absolute paths:
            if pattern.startswith("/"):
                full_path = f"/{full_path}"
            elif not full_path.startswith("/"):
                full_path = os.path.join(base_path, full_path).replace("//", "/")

            matches.append(full_path)
    return sorted(matches)


def expand_remote_globs_recursive(
    client: ops.pebble.Client | shimmer.PebbleCliClient,
    pattern: str,
    base_path: str = "/",
) -> list[str]:
    """Expand glob patterns recursively against the remote filesystem.

    This function handles patterns like "**/*.txt" for recursive matching.

    Args:
        client: Pebble client for remote filesystem access
        pattern: Glob pattern to expand (supports ** for recursion)
        base_path: Base directory to search from (default: "/")

    Returns:
        List of matching file paths
    """
    if "**" not in pattern:
        return expand_remote_globs(client, pattern, base_path)

    # Split pattern by **:
    parts = pattern.split("**")
    if len(parts) != 2:
        return [pattern]

    suffix = parts[1].lstrip("/")

    matches: list[str] = []

    def search_recursive(current_dir: str, remaining_pattern: str):
        """Recursively search directories for matches."""
        try:
            files = client.list_files(current_dir)
        except ops.pebble.PathError:
            return

        for file_info in files:
            if file_info.name in (".", ".."):
                continue

            current_path = f"{current_dir}/{file_info.name}".replace("//", "/")

            if file_info.type == ops.pebble.FileType.DIRECTORY:
                # If we have a remaining pattern, continue searching:
                if remaining_pattern:
                    search_recursive(current_path, remaining_pattern)
                else:
                    # No remaining pattern, this directory matches:
                    matches.append(current_path)
                    # Continue searching recursively for nested directories:
                    search_recursive(current_path, remaining_pattern)
            # It's a file, check if it matches the remaining pattern:
            elif not remaining_pattern or fnmatch.fnmatch(
                file_info.name, remaining_pattern
            ):
                matches.append(current_path)

    # Start recursive search:
    search_recursive(base_path, suffix)

    return sorted(matches)


def expand_globs_in_tokens(
    client: ops.pebble.Client | shimmer.PebbleCliClient,
    tokens: list[str],
    base_path: str = "/",
) -> list[str]:
    """Expand glob patterns in a list of tokens.

    Args:
        client: Pebble client for remote filesystem access
        tokens: List of command tokens
        base_path: Base directory for relative paths

    Returns:
        List of tokens with glob patterns expanded
    """
    expanded: list[str] = []

    for token in tokens:
        # Check if token contains glob patterns:
        if any(char in token for char in "*?[") and not token.startswith("-"):
            matches = expand_remote_globs(client, token, base_path)
            if matches:
                expanded.extend(matches)
            else:
                # No matches, keep original token:
                expanded.append(token)
        else:
            expanded.append(token)

    return expanded
