"""Clipboard commands for Cascade.

These commands interact with the local system clipboard, allowing users
to copy data from container inspection to their clipboard and paste
clipboard contents into commands.

Requires the optional 'clipboard' dependency:
    pip install pebble-cascade[clipboard]
"""

from .copy import CopyCommand
from .cpwd import CpwdCommand
from .pasta import PastaCommand
from .pastas import PastasCommand

__all__ = [
    "CopyCommand",
    "CpwdCommand",
    "PastaCommand",
    "PastasCommand",
]
