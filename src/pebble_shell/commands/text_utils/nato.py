"""NATO phonetic alphabet command for Cascade.

This module provides implementation for the nato command that converts
letters to their NATO phonetic alphabet equivalents.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]

# NATO phonetic alphabet
NATO_ALPHABET = {
    'A': 'Alfa',
    'B': 'Bravo',
    'C': 'Charlie',
    'D': 'Delta',
    'E': 'Echo',
    'F': 'Foxtrot',
    'G': 'Golf',
    'H': 'Hotel',
    'I': 'India',
    'J': 'Juliet',
    'K': 'Kilo',
    'L': 'Lima',
    'M': 'Mike',
    'N': 'November',
    'O': 'Oscar',
    'P': 'Papa',
    'Q': 'Quebec',
    'R': 'Romeo',
    'S': 'Sierra',
    'T': 'Tango',
    'U': 'Uniform',
    'V': 'Victor',
    'W': 'Whiskey',
    'X': 'X-ray',
    'Y': 'Yankee',
    'Z': 'Zulu',
    '0': 'Zero',
    '1': 'One',
    '2': 'Two',
    '3': 'Three',
    '4': 'Four',
    '5': 'Five',
    '6': 'Six',
    '7': 'Seven',
    '8': 'Eight',
    '9': 'Nine',
}


class NatoCommand(Command):
    """Convert text to NATO phonetic alphabet."""

    name = "nato"
    help = "Convert text to NATO phonetic alphabet"
    category = "Text Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Convert text to NATO phonetic alphabet.

Usage: nato [OPTIONS] [TEXT...]
       echo "text" | nato

Options:
    -h, --help      Show this help message
    -l, --lower     Output in lowercase
    -s, --separator SEP  Use SEP between words (default: space)

Converts letters and digits to NATO phonetic alphabet words.
Non-alphanumeric characters are passed through unchanged.

Examples:
    nato abc        # Output: Alfa Bravo Charlie
    nato "SOS"      # Output: Sierra Oscar Sierra
    nato 747        # Output: Seven Four Seven
    nato -s "-" hi  # Output: Hotel-India
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the nato command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "l": bool,
                "lower": bool,
                "s": str,
                "separator": str,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        lowercase = flags["l"] or flags["lower"]
        separator = flags["s"] or flags["separator"] or " "

        if positional_args:
            text = ' '.join(positional_args)
            self.console.print(self._convert_to_nato(text, lowercase, separator))
        else:
            # Read from stdin
            if not sys.stdin.isatty():
                for line in sys.stdin:
                    converted = self._convert_to_nato(line.rstrip(), lowercase, separator)
                    self.console.print(converted)
            else:
                self.console.print("[yellow]nato: no input provided[/yellow]")
                return 1

        return 0

    def _convert_to_nato(self, text: str, lowercase: bool, separator: str) -> str:
        """Convert text to NATO phonetic alphabet."""
        words = []
        for char in text:
            upper_char = char.upper()
            if upper_char in NATO_ALPHABET:
                word = NATO_ALPHABET[upper_char]
                if lowercase:
                    word = word.lower()
                words.append(word)
            elif char.isspace():
                # Represent spaces with a separator or skip
                continue
            else:
                # Pass through non-alphanumeric characters
                words.append(char)

        return separator.join(words)
