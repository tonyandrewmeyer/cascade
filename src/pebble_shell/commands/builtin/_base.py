"""Base classes for builtin commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ops

from ...utils.command_helpers import (
    process_file_arguments,
    validate_min_args,
)
from .._base import Command

if TYPE_CHECKING:
    from collections.abc import Callable

    import shimmer


class _HashCommand(Command):
    """Compute hash of a file or stdin."""

    category = "Filesystem Commands"

    def _hash_file(
        self,
        client: ops.pebble.Client | shimmer.PebbleCliClient,
        args: list[str],
        hash_func: Callable[..., Any],
    ):
        # Validate file arguments
        if not validate_min_args(self.shell, args, 1, f"{self.name} <file> [file2...]"):
            return 1

        # Process file arguments with path resolution
        file_paths = process_file_arguments(
            self.shell, client, args, allow_globs=False, min_files=1
        )
        if file_paths is None:
            return 1

        exit_code = 0
        for file_path in file_paths:
            try:
                with client.pull(file_path, encoding=None) as f:
                    h = hash_func()
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        h.update(chunk)
                # Use original filename from args for output, not resolved path
                original_name = args[file_paths.index(file_path)]
                self.console.print(f"{h.hexdigest()}  {original_name}")
            except (ops.pebble.PathError, ops.pebble.APIError) as e:
                self.console.print(f"{self.name}: {file_path}: {e}")
                exit_code = 1
        return exit_code
