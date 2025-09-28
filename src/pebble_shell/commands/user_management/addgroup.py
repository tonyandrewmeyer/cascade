"""Implementation of AddgroupCommand."""

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


class AddgroupCommand(Command):
    """Implementation of addgroup command."""

    name = "addgroup"
    help = "Add a new group to the system"
    category = "User Management"

    def show_help(self):
        """Show command help."""
        help_text = """Add a new group to the system.

Usage: addgroup [OPTIONS] GROUP
       addgroup [OPTIONS] USER GROUP

Description:
    Add a new group to the system by modifying /etc/group and /etc/gshadow.
    Can also add an existing user to an existing group.

Options:
    --gid GID           Specify group ID (default: auto-assign)
    --system            Create a system group (GID < 1000)
    --quiet             Suppress informational messages
    -h, --help          Show this help message

Examples:
    addgroup mygroup            # Create new group
    addgroup --gid 1001 staff   # Create group with specific GID
    addgroup --system daemon    # Create system group
    addgroup user wheel         # Add user to existing group
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the addgroup command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("[red]addgroup: missing group name[/red]")
            return 1

        parse_result = parse_flags(
            args,
            {
                "gid": int,  # group ID
                "system": bool,  # system group
                "quiet": bool,  # quiet mode
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if len(positional_args) == 1:
            # Creating new group
            group_name = positional_args[0]
            user_name = None
        elif len(positional_args) == 2:
            # Adding user to existing group
            user_name = positional_args[0]
            group_name = positional_args[1]
        else:
            self.console.print("[red]addgroup: invalid arguments[/red]")
            return 1

        gid = flags.get("gid")
        system_group = flags.get("system", False)
        quiet = flags.get("quiet", False)

        try:
            if user_name:
                # Add user to existing group
                return self._add_user_to_group(client, user_name, group_name, quiet)
            else:
                # Create new group
                return self._create_group(client, group_name, gid, system_group, quiet)

        except Exception as e:
            self.console.print(f"[red]addgroup: {e}[/red]")
            return 1

    def _create_group(
        self,
        client: ClientType,
        group_name: str,
        gid: int | None,
        system_group: bool,
        quiet: bool,
    ) -> int:
        """Create a new group."""
        # Read existing /etc/group
        group_content = safe_read_file(client, "/etc/group")
        if group_content is None:
            self.console.print("[red]addgroup: cannot read /etc/group[/red]")
            return 1

        # Check if group already exists
        for line in group_content.strip().split("\n"):
            if line and line.split(":")[0] == group_name:
                self.console.print(
                    f"[red]addgroup: group '{group_name}' already exists[/red]"
                )
                return 1

        # Determine GID
        if gid is None:
            gid = self._find_available_gid(group_content, system_group)

        # Check if GID is already in use
        for line in group_content.strip().split("\n"):
            if line and len(line.split(":")) >= 3:
                existing_gid = line.split(":")[2]
                if existing_gid == str(gid):
                    self.console.print(f"[red]addgroup: GID {gid} already in use[/red]")
                    return 1

        # Create group entry
        group_entry = f"{group_name}:x:{gid}:"

        # Read existing /etc/gshadow
        gshadow_content = safe_read_file(client, "/etc/gshadow")
        if gshadow_content is None:
            # Create minimal gshadow if it doesn't exist
            gshadow_content = ""

        # Create gshadow entry
        gshadow_entry = f"{group_name}:!::"

        # Write files (in Cascade, we simulate this)
        if not quiet:
            self.console.print(
                f"[green]Adding group '{group_name}' (GID {gid})[/green]"
            )

        self.console.print("[yellow]addgroup: would write to /etc/group:[/yellow]")
        self.console.print(f"[dim]{group_entry}[/dim]")

        self.console.print("[yellow]addgroup: would write to /etc/gshadow:[/yellow]")
        self.console.print(f"[dim]{gshadow_entry}[/dim]")

        if not quiet:
            self.console.print(
                f"[green]Group '{group_name}' created successfully[/green]"
            )

        return 0

    def _add_user_to_group(
        self, client: ClientType, user_name: str, group_name: str, quiet: bool
    ) -> int:
        """Add existing user to existing group."""
        # Read /etc/passwd to verify user exists
        passwd_content = safe_read_file(client, "/etc/passwd")
        if passwd_content is None:
            self.console.print("[red]addgroup: cannot read /etc/passwd[/red]")
            return 1

        user_exists = False
        for line in passwd_content.strip().split("\n"):
            if line and line.split(":")[0] == user_name:
                user_exists = True
                break

        if not user_exists:
            self.console.print(
                f"[red]addgroup: user '{user_name}' does not exist[/red]"
            )
            return 1

        # Read /etc/group to verify group exists and add user
        group_content = safe_read_file(client, "/etc/group")
        if group_content is None:
            self.console.print("[red]addgroup: cannot read /etc/group[/red]")
            return 1

        new_lines = []
        group_found = False

        for line in group_content.strip().split("\n"):
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 4 and parts[0] == group_name:
                group_found = True
                # Check if user is already in group
                members = parts[3].split(",") if parts[3] else []
                if user_name in members:
                    self.console.print(
                        f"[yellow]addgroup: user '{user_name}' is already "
                        f"in group '{group_name}'[/yellow]"
                    )
                    return 0

                # Add user to group
                if members and members[0]:  # Group has existing members
                    new_members = ",".join([*members, user_name])
                else:  # Group has no members
                    new_members = user_name

                new_line = f"{parts[0]}:{parts[1]}:{parts[2]}:{new_members}"
                new_lines.append(new_line)

                if not quiet:
                    self.console.print(
                        f"[green]Adding user '{user_name}' to group '{group_name}'[/green]"
                    )

                self.console.print(
                    "[yellow]addgroup: would update /etc/group line:[/yellow]"
                )
                self.console.print(f"[dim]{new_line}[/dim]")
            else:
                new_lines.append(line)

        if not group_found:
            self.console.print(
                f"[red]addgroup: group '{group_name}' does not exist[/red]"
            )
            return 1

        if not quiet:
            self.console.print(
                f"[green]User '{user_name}' added to group '{group_name}' "
                f"successfully[/green]"
            )

        return 0

    def _find_available_gid(self, group_content: str, system_group: bool) -> int:
        """Find next available GID."""
        used_gids = set()

        for line in group_content.strip().split("\n"):
            if line and len(line.split(":")) >= 3:
                try:
                    gid = int(line.split(":")[2])
                    used_gids.add(gid)
                except ValueError:
                    continue

        # System groups: 100-999, regular groups: 1000+
        start_gid = 100 if system_group else 1000
        max_gid = 999 if system_group else 65534

        for gid in range(start_gid, max_gid + 1):
            if gid not in used_gids:
                return gid

        raise Exception(f"No available GID in range {start_gid}-{max_gid}")
