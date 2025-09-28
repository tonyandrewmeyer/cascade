"""Implementation of AdduserCommand."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command
from .addgroup import AddgroupCommand

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell

# Standard Unix shadow file values
LOCKED_ACCOUNT_HASH = "!"  # Standard indicator for locked/disabled account


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class AdduserCommand(Command):
    """Implementation of adduser command."""

    name = "adduser"
    help = "Add a new user to the system"
    category = "User Management"

    def show_help(self):
        """Show command help."""
        help_text = """Add a new user to the system.

Usage: adduser [OPTIONS] USERNAME

Description:
    Add a new user to the system by modifying /etc/passwd, /etc/shadow,
    and optionally creating a home directory and default group.

Options:
    --uid UID           Specify user ID (default: auto-assign)
    --gid GID           Specify primary group ID
    --home DIR          Home directory (default: /home/USERNAME)
    --shell SHELL       Login shell (default: /bin/sh)
    --gecos GECOS       User information (full name, etc.)
    --system            Create a system user (UID < 1000)
    --no-create-home    Don't create home directory
    --disabled-password Create account with disabled password
    --quiet             Suppress informational messages
    -h, --help          Show this help message

Examples:
    adduser john                    # Create regular user
    adduser --uid 1001 jane         # Create user with specific UID
    adduser --system daemon         # Create system user
    adduser --shell /bin/bash bob   # Create user with bash shell
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the adduser command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("[red]adduser: missing username[/red]")
            return 1

        parse_result = parse_flags(
            args,
            {
                "uid": int,  # user ID
                "gid": int,  # group ID
                "home": str,  # home directory
                "shell": str,  # shell
                "gecos": str,  # user info
                "system": bool,  # system user
                "no-create-home": bool,  # don't create home
                "disabled-password": bool,  # disabled password
                "quiet": bool,  # quiet mode
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        if not positional_args:
            self.console.print("[red]adduser: missing username[/red]")
            return 1

        username = positional_args[0]
        uid = flags.get("uid")
        gid = flags.get("gid")
        home_dir = flags.get("home", f"/home/{username}")
        shell = flags.get("shell", "/bin/sh")
        gecos = flags.get("gecos", "")
        system_user = flags.get("system", False)
        no_create_home = flags.get("no-create-home", False)
        disabled_password = flags.get("disabled-password", False)
        quiet = flags.get("quiet", False)

        try:
            return self._create_user(
                client,
                username,
                uid,
                gid,
                home_dir,
                shell,
                gecos,
                system_user,
                no_create_home,
                disabled_password,
                quiet,
            )

        except Exception as e:
            self.console.print(f"[red]adduser: {e}[/red]")
            return 1

    def _create_user(
        self,
        client: ClientType,
        username: str,
        uid: int | None,
        gid: int | None,
        home_dir: str,
        shell: str,
        gecos: str,
        system_user: bool,
        no_create_home: bool,
        disabled_password: bool,
        quiet: bool,
    ) -> int:
        """Create a new user."""
        # Read existing /etc/passwd
        passwd_content = safe_read_file(client, "/etc/passwd")
        if passwd_content is None:
            self.console.print("[red]adduser: cannot read /etc/passwd[/red]")
            return 1

        # Check if user already exists
        for line in passwd_content.strip().split("\n"):
            if line and line.split(":")[0] == username:
                self.console.print(
                    f"[red]adduser: user '{username}' already exists[/red]"
                )
                return 1

        # Determine UID
        if uid is None:
            uid = self._find_available_uid(passwd_content, system_user)

        # Check if UID is already in use
        for line in passwd_content.strip().split("\n"):
            if line and len(line.split(":")) >= 3:
                existing_uid = line.split(":")[2]
                if existing_uid == str(uid):
                    self.console.print(f"[red]adduser: UID {uid} already in use[/red]")
                    return 1

        # Determine GID - create group if not specified
        if gid is None:
            # Create a group with the same name as the user
            group_result = self._create_user_group(client, username, system_user, quiet)
            if group_result != 0:
                return group_result
            gid = uid  # Use same ID for group

        # Validate that GID exists
        group_content = safe_read_file(client, "/etc/group")
        if group_content is not None:
            gid_exists = False
            for line in group_content.strip().split("\n"):
                if (
                    line
                    and len(line.split(":")) >= 3
                    and line.split(":")[2] == str(gid)
                ):
                    gid_exists = True
                    break

            if not gid_exists:
                self.console.print(
                    f"[red]adduser: group with GID {gid} does not exist[/red]"
                )
                return 1

        # Create passwd entry
        passwd_entry = f"{username}:x:{uid}:{gid}:{gecos}:{home_dir}:{shell}"

        # Read existing /etc/shadow
        shadow_content = safe_read_file(client, "/etc/shadow")
        if shadow_content is None:
            # Create minimal shadow if it doesn't exist
            shadow_content = ""

        # Create shadow entry
        if disabled_password:
            password_hash = LOCKED_ACCOUNT_HASH
        else:
            # Generate a random password hash (user will need to set password)
            password_hash = LOCKED_ACCOUNT_HASH  # Account locked until password is set

        # Get days since epoch for password age
        days_since_epoch = int(time.time() // 86400)

        shadow_entry = f"{username}:{password_hash}:{days_since_epoch}:0:99999:7:::"

        # Show what would be done
        if not quiet:
            self.console.print(
                f"[green]Adding user '{username}' (UID {uid}, GID {gid})[/green]"
            )

        self.console.print("[yellow]adduser: would write to /etc/passwd:[/yellow]")
        self.console.print(f"[dim]{passwd_entry}[/dim]")

        self.console.print("[yellow]adduser: would write to /etc/shadow:[/yellow]")
        self.console.print(f"[dim]{shadow_entry}[/dim]")

        # Create home directory
        if not no_create_home and not system_user:
            self.console.print(
                f"[yellow]adduser: would create home directory: {home_dir}[/yellow]"
            )
            self.console.print(
                f"[yellow]adduser: would set ownership to {uid}:{gid}[/yellow]"
            )

        if not quiet:
            self.console.print(f"[green]User '{username}' created successfully[/green]")
            if disabled_password:
                self.console.print(
                    "[yellow]Account created with disabled password[/yellow]"
                )
            else:
                self.console.print(
                    "[yellow]User account locked - use passwd to set password[/yellow]"
                )

        return 0

    def _create_user_group(
        self, client: ClientType, username: str, system_user: bool, quiet: bool
    ) -> int:
        """Create a group for the user."""
        # Use the addgroup command to create the group
        addgroup_cmd = AddgroupCommand(self.shell)

        args = ["--quiet"] if quiet else []
        if system_user:
            args.append("--system")
        args.append(username)

        return addgroup_cmd.execute(client, args)

    def _find_available_uid(self, passwd_content: str, system_user: bool) -> int:
        """Find next available UID."""
        used_uids = set()

        for line in passwd_content.strip().split("\n"):
            if line and len(line.split(":")) >= 3:
                try:
                    uid = int(line.split(":")[2])
                    used_uids.add(uid)
                except ValueError:
                    continue

        # System users: 100-999, regular users: 1000+
        start_uid = 100 if system_user else 1000
        max_uid = 999 if system_user else 65534

        for uid in range(start_uid, max_uid + 1):
            if uid not in used_uids:
                return uid

        raise Exception(f"No available UID in range {start_uid}-{max_uid}")
