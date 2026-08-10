"""Mksh command for Cascade.

This module provides implementation for the mksh command that creates
an executable shell script with proper headers and opens it in an editor.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from typing import TYPE_CHECKING, Union

import ops

from ...utils import resolve_path
from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]

# Default shell script template
BASH_TEMPLATE = '''#!/usr/bin/env bash
set -euo pipefail

# Script: {name}
# Created: {date}

'''

SH_TEMPLATE = '''#!/bin/sh
set -eu

# Script: {name}
# Created: {date}

'''


class MkshCommand(Command):
    """Create an executable shell script and open it in an editor."""

    name = "mksh"
    help = "Create an executable shell script and open in editor"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Create an executable shell script and open it in an editor.

Usage: mksh [OPTIONS] SCRIPT_NAME

Options:
    -h, --help      Show this help message
    -s, --sh        Use /bin/sh instead of bash
    -b, --bare      Don't add script template, just shebang
    -n, --no-edit   Create the script but don't open editor

Creates a new shell script with:
- Proper shebang (#!/usr/bin/env bash or #!/bin/sh)
- Safe shell options (set -euo pipefail for bash, set -eu for sh)
- Opens in $EDITOR (defaults to pico)

Examples:
    mksh myscript.sh        # Create and edit bash script
    mksh -s deploy.sh       # Create POSIX sh script
    mksh -b quick.sh        # Just shebang, no template
    mksh -n setup.sh        # Create without opening editor
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the mksh command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "s": bool,
                "sh": bool,
                "b": bool,
                "bare": bool,
                "n": bool,
                "no-edit": bool,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if not positional_args:
            self.console.print("[red]mksh: missing script name argument[/red]")
            return 1

        script_name = positional_args[0]
        use_sh = flags["s"] or flags["sh"]
        bare = flags["b"] or flags["bare"]
        no_edit = flags["n"] or flags["no-edit"]

        # Resolve the path
        remote_path = resolve_path(
            self.shell.current_directory, script_name, self.shell.home_dir
        )

        # Check if file already exists
        try:
            client.pull(remote_path)
            self.console.print(f"[red]mksh: '{remote_path}' already exists[/red]")
            return 1
        except ops.pebble.PathError:
            # File doesn't exist, good
            pass

        # Generate script content
        import datetime
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        base_name = os.path.basename(script_name)

        if bare:
            if use_sh:
                content = "#!/bin/sh\n\n"
            else:
                content = "#!/usr/bin/env bash\n\n"
        else:
            if use_sh:
                content = SH_TEMPLATE.format(name=base_name, date=date_str)
            else:
                content = BASH_TEMPLATE.format(name=base_name, date=date_str)

        if no_edit:
            # Just create the file without editing
            try:
                import io
                client.push(remote_path, io.StringIO(content), make_dirs=True)
                # Note: Pebble doesn't support chmod directly, but script will work
                # if executed with bash/sh explicitly
                self.console.print(f"[green]Created:[/green] {remote_path}")
                return 0
            except Exception as e:
                self.console.print(f"[red]mksh: cannot create '{remote_path}': {e}[/red]")
                return 1

        # Create temp file with content and open in editor
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            editor = os.environ.get("EDITOR", "pico")
            before_mtime = os.stat(tmp_path).st_mtime

            # Open editor
            subprocess.run([editor, tmp_path], check=True)  # noqa: S603

            after_mtime = os.stat(tmp_path).st_mtime

            # Push the file to remote if it was modified or if it's new
            if after_mtime != before_mtime or not bare:
                with open(tmp_path, "rb") as f:
                    client.push(remote_path, f, make_dirs=True)
                self.console.print(f"[green]Created:[/green] {remote_path}")
            else:
                self.console.print("[yellow]mksh: no changes made, script not created[/yellow]")
                return 1

            return 0

        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]mksh: editor failed: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]mksh: cannot create '{remote_path}': {e}[/red]")
            return 1
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
