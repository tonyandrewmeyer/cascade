"""Built-in shell commands similar to bash built-ins."""

from .alias import AliasCommand
from .beep import BeepCommand
from .bzcat import BzcatCommand
from .cal import CalCommand
from .cd import CdCommand
from .cut import CutCommand
from .date import DateCommand
from .echo import EchoCommand
from .edit import EditCommand
from .env import EnvCommand
from .false import FalseCommand
from .grep import GrepCommand
from .hd import HdCommand
from .hexdump import HexdumpCommand
from .history import HistoryCommand
from .id import IdCommand
from .info import InfoCommand
from .jq import JqCommand
from .lsof import LsofCommand
from .markdown import MarkdownCommand
from .md5sum import Md5sumCommand
from .mkpasswd import MkpasswdCommand
from .pebblesay import PebblesayCommand
from .printenv import PrintenvCommand
from .printf import PrintfCommand
from .pwd import PwdCommand
from .sha1sum import Sha1sumCommand
from .sha256sum import Sha256sumCommand
from .sha512sum import Sha512sumCommand
from .sleep import SleepCommand
from .sort import SortCommand
from .tac import TacCommand
from .time import TimeCommand
from .timeout import TimeoutCommand
from .true import TrueCommand
from .ulimit import UlimitCommand
from .uniq import UniqCommand
from .usleep import UsleepCommand
from .watch import WatchCommand
from .wc import WcCommand
from .whoami import WhoamiCommand
from .yq import YqCommand
from .zcat import ZcatCommand

__all__ = [
    "AliasCommand",
    "BeepCommand",
    "BzcatCommand",
    "CalCommand",
    "CdCommand",
    "CutCommand",
    "DateCommand",
    "EchoCommand",
    "EditCommand",
    "EnvCommand",
    "FalseCommand",
    "GrepCommand",
    "HdCommand",
    "HexdumpCommand",
    "HistoryCommand",
    "IdCommand",
    "InfoCommand",
    "JqCommand",
    "LsofCommand",
    "MarkdownCommand",
    "Md5sumCommand",
    "MkpasswdCommand",
    "PebblesayCommand",
    "PrintenvCommand",
    "PrintfCommand",
    "PwdCommand",
    "Sha1sumCommand",
    "Sha256sumCommand",
    "Sha512sumCommand",
    "SleepCommand",
    "SortCommand",
    "TacCommand",
    "TimeCommand",
    "TimeoutCommand",
    "TrueCommand",
    "UlimitCommand",
    "UniqCommand",
    "UsleepCommand",
    "WatchCommand",
    "WcCommand",
    "WhoamiCommand",
    "YqCommand",
    "ZcatCommand",
]
