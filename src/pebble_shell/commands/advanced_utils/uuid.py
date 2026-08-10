"""UUID command for Cascade.

This module provides implementation for the uuid command that generates
UUIDs (Universally Unique Identifiers).
"""

from __future__ import annotations

import uuid as uuid_module
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class UuidCommand(Command):
    """Generate a UUID."""

    name = "uuid"
    help = "Generate a UUID (Universally Unique Identifier)"
    category = "System Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Generate a UUID (Universally Unique Identifier).

Usage: uuid [OPTIONS]

Options:
    -h, --help      Show this help message
    -4, --v4        Generate a version 4 (random) UUID (default)
    -1, --v1        Generate a version 1 (time-based) UUID
    -n, --count N   Generate N UUIDs
    -u, --upper     Output in uppercase

Examples:
    uuid            # Generate a random UUID
    uuid -1         # Generate a time-based UUID
    uuid -n 5       # Generate 5 UUIDs
    uuid -u         # Generate UUID in uppercase
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the uuid command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "4": bool,
                "v4": bool,
                "1": bool,
                "v1": bool,
                "n": int,
                "count": int,
                "u": bool,
                "upper": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, _ = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        use_v1 = flags["1"] or flags["v1"]
        uppercase = flags["u"] or flags["upper"]
        count = flags["n"] or flags["count"] or 1

        for _ in range(count):
            if use_v1:
                generated_uuid = str(uuid_module.uuid1())
            else:
                generated_uuid = str(uuid_module.uuid4())

            if uppercase:
                generated_uuid = generated_uuid.upper()

            self.console.print(generated_uuid)

        return 0
