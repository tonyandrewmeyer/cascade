"""Compute SHA256 hash of a file or stdin."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ._base import _HashCommand

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class Sha256sumCommand(_HashCommand):
    """Compute SHA256 hash of a file or stdin."""

    name = "sha256sum"
    help = "Compute SHA256 hash of a file or stdin"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the sha256sum command."""
        if handle_help_flag(self, args):
            return 0
        return self._hash_file(client, args, hashlib.sha256)
