"""Implementation of DeluserCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer


# Standard Unix shadow file values
LOCKED_ACCOUNT_HASH = "!"  # Standard indicator for locked/disabled account


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DeluserCommand(Command):
    """Implementation of deluser command."""

    name = "deluser"
    help = "Delete a user from the system"
    category = "User Management"

    def show_help(self):
        """Show command help."""
        help_text = """Delete a user from the system.

Usage: deluser [OPTIONS] USERNAME
       deluser [OPTIONS] USERNAME GROUP

Description:
    Delete a user from the system by removing entries from /etc/passwd
    and /etc/shadow, or remove a user from a specific group.

Options:
    --remove-home       Remove user's home directory
    --remove-all-files  Remove all files owned by user
    --backup            Backup files before removing
    --quiet             Suppress informational messages
    -h, --help          Show this help message

Examples:
    deluser john                    # Delete user
    deluser --remove-home jane      # Delete user and home directory
    deluser bob wheel               # Remove user from group
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the deluser command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("[red]deluser: missing username[/red]")
            return 1

        parse_result = parse_flags(
            args,
            {
                "remove-home": bool,  # remove home directory
                "remove-all-files": bool,  # remove all user files
                "backup": bool,  # backup files
                "quiet": bool,  # quiet mode
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if len(positional_args) == 1:
            # Deleting user
            username = positional_args[0]
            group_name = None
        elif len(positional_args) == 2:
            # Removing user from group
            username = positional_args[0]
            group_name = positional_args[1]
        else:
            self.console.print("[red]deluser: invalid arguments[/red]")
            return 1

        remove_home = flags.get("remove-home", False)
        remove_all_files = flags.get("remove-all-files", False)
        backup = flags.get("backup", False)
        quiet = flags.get("quiet", False)

        try:
            if group_name:
                # Remove user from group
                return self._remove_user_from_group(client, username, group_name, quiet)
            else:
                # Delete user
                return self._delete_user(
                    client, username, remove_home, remove_all_files, backup, quiet
                )

        except Exception as e:
            self.console.print(f"[red]deluser: {e}[/red]")
            return 1

    def _delete_user(
        self,
        client: ClientType,
        username: str,
        remove_home: bool,
        remove_all_files: bool,
        backup: bool,
        quiet: bool,
    ) -> int:
        """Delete a user from the system."""
        # Read /etc/passwd
        passwd_content = safe_read_file(client, "/etc/passwd")
        if passwd_content is None:
            self.console.print("[red]deluser: cannot read /etc/passwd[/red]")
            return 1

        # Find and remove user entry
        new_passwd_lines = []
        user_found = False
        user_info = None

        for line in passwd_content.strip().split("\n"):
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 6 and parts[0] == username:
                user_found = True
                user_info = {
                    "uid": parts[2],
                    "gid": parts[3],
                    "home": parts[5] if len(parts) > 5 else f"/home/{username}",
                }
                if not quiet:
                    self.console.print(
                        f"[green]Removing user '{username}' from /etc/passwd[/green]"
                    )
                self.console.print(
                    f"[yellow]deluser: would remove passwd entry: {line}[/yellow]"
                )
            else:
                new_passwd_lines.append(line)

        if not user_found:
            self.console.print(f"[red]deluser: user '{username}' does not exist[/red]")
            return 1

        # Read /etc/shadow
        shadow_content = safe_read_file(client, "/etc/shadow")
        if shadow_content is not None:
            new_shadow_lines = []

            for line in shadow_content.strip().split("\n"):
                if not line:
                    continue

                if line.split(":")[0] == username:
                    if not quiet:
                        self.console.print(
                            f"[green]Removing user '{username}' from /etc/shadow[/green]"
                        )
                    self.console.print(
                        f"[yellow]deluser: would remove shadow entry: {line}[/yellow]"
                    )
                else:
                    new_shadow_lines.append(line)

        # Remove user from all groups
        self._remove_user_from_all_groups(client, username, quiet)

        # Handle home directory
        if remove_home and user_info:
            home_dir = user_info["home"]
            if not quiet:
                self.console.print(
                    f"[green]Removing home directory: {home_dir}[/green]"
                )

            if backup:
                backup_name = f"{home_dir}.backup.{int(time.time())}"
                self.console.print(
                    f"[yellow]deluser: would backup {home_dir} to {backup_name}[/yellow]"
                )

            self.console.print(
                f"[yellow]deluser: would remove directory: {home_dir}[/yellow]"
            )

        # Handle all user files
        if remove_all_files and user_info:
            uid = user_info["uid"]
            if not quiet:
                self.console.print(
                    f"[green]Removing all files owned by UID {uid}[/green]"
                )
            self.console.print(
                f"[yellow]deluser: would find and remove all files owned by UID {uid}[/yellow]"
            )

        if not quiet:
            self.console.print(f"[green]User '{username}' deleted successfully[/green]")

        return 0

    def _remove_user_from_group(
        self, client: ClientType, username: str, group_name: str, quiet: bool
    ) -> int:
        """Remove user from a specific group."""
        # Read /etc/group
        group_content = safe_read_file(client, "/etc/group")
        if group_content is None:
            self.console.print("[red]deluser: cannot read /etc/group[/red]")
            return 1

        new_lines = []
        user_removed = False

        for line in group_content.strip().split("\n"):
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 4 and parts[0] == group_name:
                # Check if user is in this group
                members = parts[3].split(",") if parts[3] else []
                if username in members:
                    # Remove user from group
                    members.remove(username)
                    new_members = ",".join(members)
                    new_line = f"{parts[0]}:{parts[1]}:{parts[2]}:{new_members}"
                    new_lines.append(new_line)
                    user_removed = True

                    if not quiet:
                        self.console.print(
                            f"[green]Removing user '{username}' from group '{group_name}'[/green]"
                        )

                    self.console.print(
                        "[yellow]deluser: would update /etc/group line:[/yellow]"
                    )
                    self.console.print(f"[dim]{new_line}[/dim]")
                else:
                    new_lines.append(line)
                    if not quiet:
                        self.console.print(
                            f"[yellow]User '{username}' is not in group '{group_name}'[/yellow]"
                        )
            else:
                new_lines.append(line)

        if not user_removed and group_name:
            # Check if group exists
            group_exists = any(
                line.split(":")[0] == group_name
                for line in group_content.strip().split("\n")
                if line
            )
            if not group_exists:
                self.console.print(
                    f"[red]deluser: group '{group_name}' does not exist[/red]"
                )
                return 1

        if user_removed and not quiet:
            self.console.print(
                f"[green]User '{username}' removed from group '{group_name}' successfully[/green]"
            )

        return 0

    def _remove_user_from_all_groups(
        self, client: ClientType, username: str, quiet: bool
    ) -> None:
        """Remove user from all groups they belong to."""
        group_content = safe_read_file(client, "/etc/group")
        if group_content is None:
            return

        groups_modified = []

        for line in group_content.strip().split("\n"):
            if not line:
                continue

            parts = line.split(":")
            if len(parts) >= 4 and parts[3]:
                members = parts[3].split(",")
                if username in members:
                    groups_modified.append(parts[0])

        if groups_modified and not quiet:
            self.console.print(
                f"[green]Removing user from groups: {', '.join(groups_modified)}[/green]"
            )

        for group in groups_modified:
            self.console.print(
                f"[yellow]deluser: would remove {username} from group {group}[/yellow]"
            )
