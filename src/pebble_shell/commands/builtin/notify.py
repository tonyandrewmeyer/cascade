"""Notify command for Cascade.

This module provides implementation for the notify command that sends
desktop notifications on the local system.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class NotifyCommand(Command):
    """Send desktop notifications."""

    name = "notify"
    help = "Send desktop notifications"
    category = "Built-in Commands"

    def show_help(self):
        """Show command help."""
        help_text = """Send desktop notifications.

Usage: notify [OPTIONS] MESSAGE

Options:
    -h, --help          Show this help message
    -t, --title TITLE   Notification title (default: "Cascade")
    -s, --subtitle SUB  Subtitle (macOS only)

Arguments:
    MESSAGE             Notification message text

Uses platform-specific notification systems:
    macOS:  AppleScript notifications or terminal-notifier
    Linux:  notify-send (libnotify)
    Windows: PowerShell toast notifications

Examples:
    notify "Build complete!"
    notify -t "Cascade" "Task finished"
    notify -t "Alert" -s "Important" "Check this out"
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the notify command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "t": str,
                "title": str,
                "s": str,
                "subtitle": str,
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
            self.console.print("[red]notify: missing message argument[/red]")
            self.console.print("Usage: notify <message>")
            return 1

        message = " ".join(positional_args)
        title = flags["t"] or flags["title"] or "Cascade"
        subtitle = flags["s"] or flags["subtitle"]

        success = self._send_notification(title, message, subtitle)

        if not success:
            self.console.print("[yellow]notify: could not send notification[/yellow]")
            self.console.print("[dim]Notification systems vary by platform[/dim]")
            # Still print the message as fallback
            self.console.print(f"\n[bold]{title}[/bold]")
            if subtitle:
                self.console.print(f"[dim]{subtitle}[/dim]")
            self.console.print(message)
            return 1

        return 0

    def _send_notification(
        self, title: str, message: str, subtitle: str | None
    ) -> bool:
        """Send a notification using platform-specific methods."""
        system = platform.system()

        if system == "Darwin":
            return self._notify_macos(title, message, subtitle)
        elif system == "Linux":
            return self._notify_linux(title, message, subtitle)
        elif system == "Windows":
            return self._notify_windows(title, message, subtitle)

        return False

    def _notify_macos(
        self, title: str, message: str, subtitle: str | None
    ) -> bool:
        """Send notification on macOS."""
        # Try terminal-notifier first (better features)
        if shutil.which("terminal-notifier"):
            cmd = [
                "terminal-notifier",
                "-title", title,
                "-message", message,
            ]
            if subtitle:
                cmd.extend(["-subtitle", subtitle])

            try:
                subprocess.run(cmd, check=True, capture_output=True)  # noqa: S603
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        # Fall back to AppleScript
        if subtitle:
            script = f'''
                display notification "{message}" with title "{title}" subtitle "{subtitle}"
            '''
        else:
            script = f'''
                display notification "{message}" with title "{title}"
            '''

        try:
            # S603, S607: osascript is a standard macOS system command
            subprocess.run(  # noqa: S603
                ["osascript", "-e", script],  # noqa: S607
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _notify_linux(
        self, title: str, message: str, subtitle: str | None
    ) -> bool:
        """Send notification on Linux using notify-send."""
        if not shutil.which("notify-send"):
            return False

        # Combine subtitle with message if present
        full_message = message
        if subtitle:
            full_message = f"{subtitle}\n{message}"

        try:
            # S603, S607: notify-send is a standard Linux notification command
            subprocess.run(  # noqa: S603
                ["notify-send", title, full_message],  # noqa: S607
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _notify_windows(
        self, title: str, message: str, subtitle: str | None
    ) -> bool:
        """Send notification on Windows using PowerShell."""
        if not shutil.which("powershell"):
            return False

        # Combine subtitle with message if present
        full_message = message
        if subtitle:
            full_message = f"{subtitle}\\n{message}"

        # PowerShell toast notification
        script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{title}</text>
                        <text id="2">{full_message}</text>
                    </binding>
                </visual>
            </toast>
"@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Cascade").Show($toast)
        '''

        try:
            # S603, S607: powershell is a standard Windows command
            subprocess.run(  # noqa: S603
                ["powershell", "-Command", script],  # noqa: S607
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
