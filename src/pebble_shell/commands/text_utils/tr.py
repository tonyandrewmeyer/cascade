"""Tr command for Cascade.

This module provides implementation for the tr command that translates
or deletes characters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


# TODO: Move this to an exceptions.py module.
class TextUtilsError(Exception):
    """Exception raised for text processing errors."""


class TrCommand(Command):
    """Implementation of tr command."""

    name = "tr"
    help = "Translate or delete characters"
    category = "Text"

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the tr command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "d": bool,  # delete characters
                "s": bool,  # squeeze repeats
                "c": bool,  # complement first set
                "C": bool,  # complement first set (same as -c)
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        delete_chars = flags.get("d", False)
        squeeze_repeats = flags.get("s", False)
        complement = flags.get("c", False) or flags.get("C", False)

        try:
            if delete_chars:
                if len(positional_args) < 1:
                    raise TextUtilsError("missing character set for delete")
                char_set = positional_args[0]
                file_args = positional_args[1:]
            else:
                if len(positional_args) < 2:
                    raise TextUtilsError("missing character sets for translation")
                set1 = positional_args[0]
                set2 = positional_args[1]
                file_args = positional_args[2:]

            if not file_args:
                self.console.print(
                    get_theme().warning_text("tr: reading from stdin not supported")
                )
                return 1

            for file_path in file_args:
                content = safe_read_file(client, file_path, self.shell)
                if content is None:
                    return 1

                if delete_chars:
                    result = self._delete_chars(
                        content, char_set, complement, squeeze_repeats
                    )
                else:
                    result = self._translate_chars(
                        content, set1, set2, complement, squeeze_repeats
                    )

                self.console.print(result, end="")

            return 0

        except (ValueError, TextUtilsError) as e:
            self.console.print(get_theme().error_text(f"tr: {e}"))
            return 1

    def _expand_char_set(self, char_set: str) -> str:
        """Expand character set expressions like 'a-z'."""
        result = ""
        i = 0
        while i < len(char_set):
            if i + 2 < len(char_set) and char_set[i + 1] == "-":
                # Range expression
                start = ord(char_set[i])
                end = ord(char_set[i + 2])
                for code in range(start, end + 1):
                    result += chr(code)
                i += 3
            else:
                result += char_set[i]
                i += 1
        return result

    def _delete_chars(
        self, content: str, char_set: str, complement: bool, squeeze: bool
    ) -> str:
        """Delete characters from content."""
        expanded_set = set(self._expand_char_set(char_set))

        if complement:
            # Delete everything except the specified set
            delete_set = set(chr(i) for i in range(256)) - expanded_set
        else:
            delete_set = expanded_set

        result = ""
        for char in content:
            if char not in delete_set:
                result += char

        if squeeze:
            # Squeeze consecutive characters that are the same
            squeezed = ""
            prev_char = None
            for char in result:
                if char != prev_char:
                    squeezed += char
                    prev_char = char
            result = squeezed

        return result

    def _translate_chars(
        self, content: str, set1: str, set2: str, complement: bool, squeeze: bool
    ) -> str:
        """Translate characters in content."""
        expanded_set1 = self._expand_char_set(set1)
        expanded_set2 = self._expand_char_set(set2)

        # Create translation table
        trans_table = {}

        if complement:
            # Translate everything except set1 to set2
            all_chars = set(chr(i) for i in range(256))
            complement_chars = all_chars - set(expanded_set1)

            if expanded_set2:
                trans_char = expanded_set2[-1]  # Use last character of set2
                for char in complement_chars:
                    trans_table[char] = trans_char
        else:
            # Normal translation
            for i, char in enumerate(expanded_set1):
                if i < len(expanded_set2):
                    trans_table[char] = expanded_set2[i]
                elif expanded_set2:
                    # Use last character of set2 for remaining chars in set1
                    trans_table[char] = expanded_set2[-1]

        result = ""
        for char in content:
            result += trans_table.get(char, char)

        if squeeze:
            # Squeeze consecutive characters that are the same
            squeezed = ""
            prev_char = None
            for char in result:
                if char != prev_char:
                    squeezed += char
                    prev_char = char
            result = squeezed

        return result
