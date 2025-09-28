"""Text processing and manipulation commands."""

from .dos2unix import Dos2unixCommand
from .expand import ExpandCommand
from .fold import FoldCommand
from .seq import SeqCommand
from .tr import TrCommand
from .unexpand import UnexpandCommand
from .unix2dos import Unix2dosCommand

__all__ = [
    "Dos2unixCommand",
    "ExpandCommand",
    "FoldCommand",
    "SeqCommand",
    "TrCommand",
    "UnexpandCommand",
    "Unix2dosCommand",
]
