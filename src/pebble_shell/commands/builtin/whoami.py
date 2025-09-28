"""Implementation of WhoamiCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import (
    ProcReadError,
    get_user_name_for_uid,
    read_proc_status_field,
)
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class WhoamiCommand(Command):
    """Command for displaying the current user."""

    name = "whoami"
    help = "Show current user"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the whoami command to display current user information."""
        if handle_help_flag(self, args):
            return 0

        try:
            uid = read_proc_status_field(client, "self", "Uid")
            if uid:
                username = get_user_name_for_uid(client, uid)
                self.console.print(f"uid={uid}({username})")
                return 0
        except ProcReadError:
            pass

        self.console.print("unknown")
        return 1
