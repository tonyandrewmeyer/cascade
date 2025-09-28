"""Implementation of CryptpwCommand."""

from __future__ import annotations

import crypt
import getpass
from typing import TYPE_CHECKING, Union

import ops

from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to System category.
class CryptpwCommand(Command):
    """Encrypt passwords using crypt()."""

    name = "cryptpw"
    help = "Encrypt passwords using crypt()"
    category = "System"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the cryptpw command."""
        return self._execute_cryptpw(client, args)

    def _execute_cryptpw(self, client: ClientType, args: list[str]) -> int:
        password = args[0] if args else getpass.getpass("Password: ")

        salt = args[1] if len(args) > 1 else None

        encrypted = crypt.crypt(password, salt)
        self.console.print(encrypted)
        return 0
