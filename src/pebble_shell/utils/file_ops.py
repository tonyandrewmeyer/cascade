"""File operation utilities for safe file handling with Pebble clients."""

from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    import shimmer
    from rich.console import Console
    from rich.progress import Progress

    PebbleClient = ops.pebble.Client | shimmer.PebbleCliClient


def safe_pull_file(client: PebbleClient, path: str) -> str | bytes | None:
    """Safely pull a file with proper error handling.

    Args:
        client: Pebble client
        path: Path to file to pull

    Returns:
        File content as string or bytes, or None if error
    """
    try:
        with client.pull(path) as file:
            return file.read()
    except (ops.pebble.PathError, ops.pebble.APIError):
        return None


def safe_push_file(
    client: PebbleClient, path: str, content: str | bytes, make_dirs: bool = True
) -> bool:
    """Safely push a file with proper error handling.

    Args:
        client: Pebble client
        path: Destination path
        content: Content to write
        make_dirs: Whether to create parent directories

    Returns:
        True if successful, False otherwise
    """
    try:
        client.push(path, content, make_dirs=make_dirs)
        return True
    except (ops.pebble.PathError, ops.pebble.APIError):
        return False


def list_directory_safe(
    client: PebbleClient, path: str
) -> list[ops.pebble.FileInfo] | None:
    """List directory contents with error handling.

    Args:
        client: Pebble client
        path: Directory path to list

    Returns:
        List of FileInfo objects, or None if error
    """
    try:
        return client.list_files(path)
    except (ops.pebble.PathError, ops.pebble.APIError):
        return None


def file_exists(client: PebbleClient, path: str) -> bool:
    """Check if a file or directory exists.

    Args:
        client: Pebble client
        path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    try:
        # Try to get the parent directory and check if file exists in it
        path_obj = pathlib.Path(path)
        parent = str(path_obj.parent) if path_obj.parent != path_obj else "."
        filename = path_obj.name

        files = client.list_files(parent)
        return any(f.name == filename for f in files)
    except (ops.pebble.PathError, ops.pebble.APIError):
        return False


def get_file_info(client: PebbleClient, path: str) -> ops.pebble.FileInfo | None:
    """Get file information for a specific path.

    Args:
        client: Pebble client
        path: Path to get info for

    Returns:
        FileInfo object if found, None otherwise
    """
    try:
        path_obj = pathlib.Path(path)
        parent = str(path_obj.parent) if path_obj.parent != path_obj else "."
        filename = path_obj.name

        files = client.list_files(parent)
        for file_info in files:
            if file_info.name == filename:
                return file_info
        return None
    except (ops.pebble.PathError, ops.pebble.APIError):
        return None


def copy_file_with_progress(
    client: PebbleClient,
    console: Console,
    source: str,
    dest: str,
    progress: Progress | None = None,
    task_id: int | None = None,
) -> bool:
    """Copy a single file with optional progress tracking.

    Args:
        client: Pebble client
        console: Console for output
        source: Source file path
        dest: Destination file path
        progress: Optional Progress instance
        task_id: Optional task ID for progress tracking

    Returns:
        True if successful, False otherwise
    """
    try:
        try:
            with client.pull(source) as file:
                content = file.read()
        except (ops.pebble.PathError, ops.pebble.APIError):
            console.print(f"cannot read source file: {source}")
            return False

        if not safe_push_file(client, dest, content, make_dirs=True):
            console.print(f"cannot write destination file: {dest}")
            return False

        console.print(f"'{source}' -> '{dest}'")

        if progress and task_id is not None:
            progress.advance(task_id)

        return True

    except Exception as e:
        console.print(f"cannot copy file: {e}")
        return False


def copy_directory_recursive(
    client: PebbleClient,
    console: Console,
    source: str,
    dest: str,
    progress: Progress | None = None,
    task_id: int | None = None,
) -> bool:
    """Copy a directory recursively with optional progress tracking.

    Args:
        client: Pebble client
        console: Console for output
        source: Source directory path
        dest: Destination directory path
        progress: Optional Progress instance
        task_id: Optional task ID for progress tracking

    Returns:
        True if successful, False otherwise
    """
    try:
        client.make_dir(dest, make_parents=True)
        console.print(f"'{source}' -> '{dest}' (directory)")

        files = list_directory_safe(client, source)
        if files is None:
            console.print(f"cannot list directory: {source}")
            return False

        success = True
        for file_info in files:
            src_path = os.path.join(source, file_info.name)
            dst_path = os.path.join(dest, file_info.name)

            if file_info.type == ops.pebble.FileType.FILE:
                if not copy_file_with_progress(
                    client, console, src_path, dst_path, progress, task_id
                ):
                    success = False
            elif (
                file_info.type == ops.pebble.FileType.DIRECTORY
                and not copy_directory_recursive(
                    client, console, src_path, dst_path, progress, task_id
                )
            ):
                success = False

        return success

    except Exception as e:
        console.print(f"cannot copy directory: {e}")
        return False


def remove_file_recursive(
    client: PebbleClient,
    console: Console,
    path: str,
    force: bool = False,
    progress: Progress | None = None,
    task_id: int | None = None,
) -> bool:
    """Remove files or directories recursively with proper error handling.

    Args:
        client: Pebble client
        console: Console for output
        path: Path to remove
        force: Whether to ignore errors
        progress: Optional Progress instance
        task_id: Optional task ID for progress tracking

    Returns:
        True if successful, False otherwise
    """
    try:
        file_info = get_file_info(client, path)
        if file_info is None:
            if not force:
                console.print(f"cannot remove '{path}': file not found")
                return False
            return True

        if file_info.type == ops.pebble.FileType.DIRECTORY:
            # Remove directory contents first.
            files = list_directory_safe(client, path)
            if files is not None:
                for sub_file in files:
                    sub_path = os.path.join(path, sub_file.name)
                    if (
                        not remove_file_recursive(
                            client, console, sub_path, force, progress, task_id
                        )
                        and not force
                    ):
                        return False

        # Remove the item itself.
        try:
            client.remove_path(path)
            console.print(f"removed '{path}'")

            if progress and task_id is not None:
                progress.advance(task_id)

            return True

        except (ops.pebble.PathError, ops.pebble.APIError) as e:
            if not force:
                console.print(f"cannot remove '{path}': {e}")
                return False
            return True

    except Exception as e:
        if not force:
            console.print(f"cannot remove '{path}': {e}")
            return False
        return True


def move_file_with_progress(
    client: PebbleClient,
    console: Console,
    source: str,
    dest: str,
    progress: Progress | None = None,
    task_id: int | None = None,
) -> bool:
    """Move a file or directory with optional progress tracking.

    This implements move as copy + delete since Pebble doesn't have native move.

    Args:
        client: Pebble client
        console: Console for output
        source: Source path
        dest: Destination path
        progress: Optional Progress instance
        task_id: Optional task ID for progress tracking

    Returns:
        True if successful, False otherwise
    """
    file_info = get_file_info(client, source)
    if file_info is None:
        console.print(f"cannot stat '{source}': file not found")
        return False

    # Copy to destination.
    if file_info.type == ops.pebble.FileType.FILE:
        if not copy_file_with_progress(
            client, console, source, dest, progress, task_id
        ):
            return False
    elif file_info.type == ops.pebble.FileType.DIRECTORY:
        if not copy_directory_recursive(
            client, console, source, dest, progress, task_id
        ):
            return False
    else:
        console.print(f"'{source}': unsupported file type")
        return False

    # Remove source.
    if not remove_file_recursive(client, console, source, force=False):
        console.print(f"moved to '{dest}' but failed to remove source '{source}'")
        return False

    return True


def ensure_parent_directory(client: PebbleClient, file_path: str) -> bool:
    """Ensure the parent directory of a file path exists.

    Args:
        client: Pebble client
        file_path: File path whose parent should exist

    Returns:
        True if parent exists or was created, False otherwise
    """
    try:
        parent = os.path.dirname(file_path)
        if parent and parent != file_path:
            client.make_dir(parent, make_parents=True)
        return True
    except (ops.pebble.PathError, ops.pebble.APIError):
        return False


def get_directory_size(client: PebbleClient, path: str) -> int:
    """Get the total size of files in a directory recursively.

    Args:
        client: Pebble client
        path: Directory path

    Returns:
        Total size in bytes, or 0 if error
    """
    total_size = 0

    try:
        files = list_directory_safe(client, path)
        if files is None:
            return 0

        for file_info in files:
            if file_info.type == ops.pebble.FileType.FILE:
                total_size += file_info.size or 0
            elif file_info.type == ops.pebble.FileType.DIRECTORY:
                sub_path = os.path.join(path, file_info.name)
                total_size += get_directory_size(client, sub_path)

    except (ops.pebble.PathError, ops.pebble.APIError):
        pass

    return total_size


def count_files_recursive(client: PebbleClient, path: str) -> int:
    """Count the total number of files in a directory recursively.

    Args:
        client: Pebble client
        path: Directory path

    Returns:
        Total file count, or 0 if error
    """
    count = 0

    try:
        files = list_directory_safe(client, path)
        if files is None:
            return 0

        for file_info in files:
            if file_info.type == ops.pebble.FileType.FILE:
                count += 1
            elif file_info.type == ops.pebble.FileType.DIRECTORY:
                sub_path = os.path.join(path, file_info.name)
                count += count_files_recursive(client, sub_path)

    except (ops.pebble.PathError, ops.pebble.APIError):
        pass

    return count
