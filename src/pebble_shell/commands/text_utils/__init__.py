"""Text processing and manipulation commands."""

from .dos2unix import Dos2unixCommand
from .expand import ExpandCommand
from .fold import FoldCommand
from .jsonformat import JsonformatCommand
from .length import LengthCommand
from .line import LineCommand
from .lowered import LoweredCommand
from .markdownquote import MarkdownquoteCommand
from .seq import SeqCommand
from .straightquote import StraightquoteCommand
from .uppered import UpperedCommand
from .tr import TrCommand
from .unexpand import UnexpandCommand
from .unix2dos import Unix2dosCommand

__all__ = [
    "Dos2unixCommand",
    "ExpandCommand",
    "FoldCommand",
    "JsonformatCommand",
    "LengthCommand",
    "LineCommand",
    "LoweredCommand",
    "MarkdownquoteCommand",
    "SeqCommand",
    "StraightquoteCommand",
    "TrCommand",
    "UnexpandCommand",
    "Unix2dosCommand",
    "UpperedCommand",
]
