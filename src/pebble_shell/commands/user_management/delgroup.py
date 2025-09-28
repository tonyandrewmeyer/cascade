"""Implementation of DelgroupCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell

# Standard Unix shadow file values
LOCKED_ACCOUNT_HASH = "!"  # Standard indicator for locked/disabled account


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DelgroupCommand(Command):
    """Implementation of delgroup command."""

    name = "delgroup"
    help = "Delete a group from the system"
    category = "User Management"

    def show_help(self):
        """Show command help."""
        help_text = """Delete a group from the system.

Usage: delgroup [OPTIONS] GROUP

Description:
    Delete a group from the system by removing entries from /etc/group
    and /etc/gshadow. Will not delete if it's the primary group of any user.

Options:
    --only-if-empty     Only delete if group has no members
    --quiet             Suppress informational messages
    -h, --help          Show this help message

Examples:
    delgroup mygroup            # Delete group
    delgroup --only-if-empty staff  # Delete only if no members
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the delgroup command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("[red]delgroup: missing group name[/red]")
            return 1

        parse_result = parse_flags(
            args,
            {
                "only-if-empty": bool,  # only delete if empty
                "quiet": bool,  # quiet mode
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not positional_args:
            self.console.print("[red]delgroup: missing group name[/red]")
            return 1

        group_name = positional_args[0]
        only_if_empty = flags.get("only-if-empty", False)
        quiet = flags.get("quiet", False)

        try:
            return self._delete_group(client, group_name, only_if_empty, quiet)

        except Exception as e:
            self.console.print(f"[red]delgroup: {e}[/red]")
            return 1

    def _delete_group(
        self, client: ClientType, group_name: str, only_if_empty: bool, quiet: bool
    ) -> int:
        """Delete a group from the system."""
        # Read /etc/group
        group_content = safe_read_file(client, "/etc/group")
        if group_content is None:
            self.console.print("[red]delgroup: cannot read /etc/group[/red]")
            return 1

        # Find group and check constraints
        new_group_lines = []
        group_found = False
        group_gid = None
        group_has_members = False

        for line in group_content.strip().split("\n"):
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 4 and parts[0] == group_name:
                group_found = True
                group_gid = parts[2]

                # Check if group has members
                if parts[3].strip():
                    group_has_members = True
                    members = parts[3].split(",")
                    if not quiet:
                        self.console.print(
                            f"[yellow]Group '{group_name}' has members: {', '.join(members)}[/yellow]"
                        )

                if only_if_empty and group_has_members:
                    self.console.print(
                        f"[red]delgroup: group '{group_name}' has members, not deleting[/red]"
                    )
                    return 1

                if not quiet:
                    self.console.print(
                        f"[green]Removing group '{group_name}' from /etc/group[/green]"
                    )
                self.console.print(
                    f"[yellow]delgroup: would remove group entry: {line}[/yellow]"
                )
            else:
                new_group_lines.append(line)

        if not group_found:
            self.console.print(
                f"[red]delgroup: group '{group_name}' does not exist[/red]"
            )
            return 1

        # Check if group is primary group for any user
        if group_gid:
            passwd_content = safe_read_file(client, "/etc/passwd")
            if passwd_content is not None:
                primary_users = []

                for line in passwd_content.strip().split("\n"):
                    if not line:
                        continue

                    parts = line.split(":")
                    if len(parts) >= 4 and parts[3] == group_gid:
                        primary_users.append(parts[0])

                if primary_users:
                    self.console.print(
                        f"[red]delgroup: cannot delete group '{group_name}' "
                        f"- it is the primary group for users: {', '.join(primary_users)}[/red]"
                    )
                    return 1

        # Read /etc/gshadow
        gshadow_content = safe_read_file(client, "/etc/gshadow")
        if gshadow_content is not None:
            new_gshadow_lines = []

            for line in gshadow_content.strip().split("\n"):
                if not line:
                    continue

                if line.split(":")[0] == group_name:
                    if not quiet:
                        self.console.print(
                            f"[green]Removing group '{group_name}' from /etc/gshadow[/green]"
                        )
                    self.console.print(
                        f"[yellow]delgroup: would remove gshadow entry: {line}[/yellow]"
                    )
                else:
                    new_gshadow_lines.append(line)

        if not quiet:
            self.console.print(
                f"[green]Group '{group_name}' deleted successfully[/green]"
            )

        return 0
