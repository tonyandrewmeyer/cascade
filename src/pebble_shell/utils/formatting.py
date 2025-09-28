"""Formatting utilities for Pebble shell output."""

from __future__ import annotations

import datetime

import ops


def _octal_permissions(permissions: int) -> str:
    """Convert integer permissions to rwxrw-r-- format."""
    return "".join(
        (
            "r" if permissions & 0o400 else "-",
            "w" if permissions & 0o200 else "-",
            "x" if permissions & 0o100 else "-",
            "r" if permissions & 0o040 else "-",
            "w" if permissions & 0o020 else "-",
            "x" if permissions & 0o010 else "-",
            "r" if permissions & 0o004 else "-",
            "w" if permissions & 0o002 else "-",
            "x" if permissions & 0o001 else "-",
        )
    )


def format_file_info(file_info: ops.pebble.FileInfo) -> str:
    """Format file information for display.

    Args:
        file_info: File information from Pebble

    Returns:
        Formatted string representation
    """
    type_char = "d" if file_info.type == ops.pebble.FileType.DIRECTORY else "-"
    permissions = _octal_permissions(file_info.permissions)
    size_str = str(file_info.size) if file_info.size is not None else "0"
    if file_info.last_modified:
        mod_time = file_info.last_modified.strftime("%b %d %H:%M")
    else:
        mod_time = "unknown"
    owner = str(file_info.user_id) if file_info.user_id is not None else "0"
    group = str(file_info.group_id) if file_info.group_id is not None else "0"
    return f"{type_char}{permissions} {owner:<8} {group:<8} {size_str:>8} {mod_time} {file_info.name}"


def format_stat_info(file_info: ops.pebble.FileInfo, path: str) -> str:
    """Format detailed file statistics.

    Args:
        file_info: File information from Pebble
        path: File path

    Returns:
        Formatted statistics string
    """
    lines = [
        f"File: {path}",
        f"Type: {file_info.type}",
        f"Size: {file_info.size} bytes"
        if file_info.size is not None
        else "Size: unknown",
    ]
    if file_info.user_id is not None:
        lines.append(f"Owner: {file_info.user_id}")
    if file_info.group_id is not None:
        lines.append(f"Group: {file_info.group_id}")
    if file_info.last_modified:
        lines.append(f"Last Modified: {file_info.last_modified}")
    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format error message.

    Args:
        message: Error message

    Returns:
        Formatted error message
    """
    return f"Error: {message}"


def format_bytes(size: int) -> str:
    """Format byte size in human-readable format.

    Args:
        size: Size in bytes

    Returns:
        Human-readable size string
    """
    human_size: float = size
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if human_size < 1024.0:
            return f"{size:.1f}{unit}"
        human_size /= 1024.0
    return f"{human_size:.1f}PB"


def format_time(seconds: int) -> str:
    """Format time duration."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_relative_time(dt: datetime.datetime) -> str:
    """Format relative time."""
    if not dt:
        return "unknown"
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=dt.tzinfo)
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} ago"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} ago"
    years = months // 12
    return f"{years} year{'s' if years != 1 else ''} ago"
