"""Compute SHA1 hash of a file or stdin."""

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


class Sha1sumCommand(_HashCommand):
    """Compute SHA1 hash of a file or stdin."""

    name = "sha1sum"
    help = "Compute SHA1 hash of a file or stdin"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the sha1sum command."""
        if handle_help_flag(self, args):
            return 0
        return self._hash_file(client, args, hashlib.sha1)
