"""Implementation of MkpasswdCommand."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class MkpasswdCommand(Command):
    """Command for generating password hashes."""
    name = "mkpasswd"
    help = "Generate password hash"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ) -> int:
        """Execute the mkpasswd command to generate password hashes."""
        if handle_help_flag(self, args):
            return 0

        result = parse_flags(
            args,
            {
                "m": str,  # method
                "method": str,
                "S": str,  # salt
                "salt": str,
                "R": int,  # rounds
                "rounds": int,
                "P": bool,  # stdin
                "stdin": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        method = flags.get("m") or flags.get("method", "des")
        salt = flags.get("S") or flags.get("salt")
        rounds = flags.get("R") or flags.get("rounds")
        read_stdin = flags.get("P", False) or flags.get("stdin", False)

        if method == "help":
            self.console.print("Available methods:")
            self.console.print("  des      DES crypt (default)")
            self.console.print("  md5      MD5 crypt")
            self.console.print("  sha256   SHA-256 crypt")
            self.console.print("  sha512   SHA-512 crypt")
            return 0

        # Get password
        if read_stdin:
            try:
                password = sys.stdin.read().strip()
            except KeyboardInterrupt:
                return 1
        elif positional_args:
            password = positional_args[0]
            if len(positional_args) > 1:
                salt = positional_args[1]
        else:
            self.console.print(
                get_theme().error_text("mkpasswd: no password specified")
            )
            return 1

        try:
            import crypt
            import secrets
            import string

            # Generate salt if not provided
            if not salt:
                if method == "des":
                    salt = "".join(
                        secrets.choice(string.ascii_letters + string.digits + "./")
                        for _ in range(2)
                    )
                elif method == "md5":
                    salt = (
                        "$1$"
                        + "".join(
                            secrets.choice(string.ascii_letters + string.digits + "./")
                            for _ in range(8)
                        )
                        + "$"
                    )
                elif method == "sha256":
                    salt = "$5$"
                    if rounds:
                        salt += f"rounds={rounds}$"
                    salt += (
                        "".join(
                            secrets.choice(string.ascii_letters + string.digits + "./")
                            for _ in range(16)
                        )
                        + "$"
                    )
                elif method == "sha512":
                    salt = "$6$"
                    if rounds:
                        salt += f"rounds={rounds}$"
                    salt += (
                        "".join(
                            secrets.choice(string.ascii_letters + string.digits + "./")
                            for _ in range(16)
                        )
                        + "$"
                    )
                else:
                    self.console.print(
                        get_theme().error_text(f"mkpasswd: unknown method '{method}'")
                    )
                    return 1

            # Generate hash
            hashed = crypt.crypt(password, salt)
            if hashed:
                self.console.print(hashed)
                return 0
            else:
                self.console.print(get_theme().error_text("mkpasswd: crypt failed"))
                return 1

        except ImportError:
            self.console.print(
                get_theme().error_text("mkpasswd: crypt module not available")
            )
            return 1
        except Exception as e:
            self.console.print(get_theme().error_text(f"mkpasswd: {e}"))
            return 1
