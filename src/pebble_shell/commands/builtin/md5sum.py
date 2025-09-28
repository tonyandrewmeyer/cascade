"""Compute MD5 hash of a file or stdin."""

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


class Md5sumCommand(_HashCommand):
    """Compute MD5 hash of a file or stdin."""

    name = "md5sum"
    help = "Compute MD5 hash of a file or stdin"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the md5sum command."""
        if handle_help_flag(self, args):
            return 0
        return self._hash_file(client, args, hashlib.md5)
