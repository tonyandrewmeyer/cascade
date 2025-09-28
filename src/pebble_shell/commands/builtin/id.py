"""Implementation of IdCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from ...utils.proc_reader import ProcReadError
from .._base import Command

if TYPE_CHECKING:
    import shimmer

# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class IdCommand(Command):
    """Command for displaying user and group IDs."""
    name = "id"
    help = "Show user and group IDs"
    category = "Built-in Commands"

    def execute(
        self, client: ops.pebble.Client | shimmer.PebbleCliClient, args: list[str]
    ):
        """Execute the id command to show user and group IDs."""
        if handle_help_flag(self, args):
            return 0

        try:
            status_fields = read_proc_status_fields(client, "self", ["Uid", "Gid"])

            # Extract real UID and GID (first value in each field)
            uid = "0"
            gid = "0"

            if "Uid" in status_fields:
                uid_parts = status_fields["Uid"].split()
                if uid_parts:
                    uid = uid_parts[0]

            if "Gid" in status_fields:
                gid_parts = status_fields["Gid"].split()
                if gid_parts:
                    gid = gid_parts[0]

            uid_name = get_user_name_for_uid(client, uid)
            gid_name = get_group_name_for_gid(client, gid)

            uid_str = f"uid={uid}({uid_name})" if uid_name else f"uid={uid}"
            gid_str = f"gid={gid}({gid_name})" if gid_name else f"gid={gid}"

            self.console.print(f"{uid_str} {gid_str}")
            return 0

        except ProcReadError:
            self.console.print("uid=0 gid=0")
            return 1
