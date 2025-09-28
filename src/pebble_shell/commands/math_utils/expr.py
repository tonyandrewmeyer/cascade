"""Implementation of ExprCommand."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag
from .._base import Command
from .exceptions import CalculationError

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class ExprCommand(Command):
    """Implementation of expr command."""

    name = "expr"
    help = "Evaluate expressions"
    category = "Mathematical Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Evaluate expressions.

Usage: expr EXPRESSION

Description:
    Print the value of EXPRESSION to standard output.

Operators (in order of increasing precedence):
    |               Boolean OR
    &               Boolean AND
    <, <=, =, !=, >=, >  Relational operators
    +, -            Addition, subtraction
    *, /, %         Multiplication, division, remainder
    :               String matching

String operations:
    STRING : REGEXP     String matching (returns match length or 0)
    length STRING       Length of string
    substr STRING POS LENGTH  Substring

Examples:
    expr 1 + 2          # Outputs: 3
    expr 10 / 3         # Outputs: 3
    expr 10 % 3         # Outputs: 1
    expr 5 \\> 3        # Outputs: 1 (true)
    expr length hello   # Outputs: 5
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the expr command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            self.console.print("[red]expr: missing operand[/red]")
            return 1

        try:
            result = self._evaluate_expression(args)

            if isinstance(result, bool):
                self.console.print("1" if result else "0")
            elif isinstance(result, float) and result.is_integer():
                self.console.print(str(int(result)))
            else:
                self.console.print(str(result))

            if isinstance(result, int | float):
                return 0 if result != 0 else 1
            elif isinstance(result, str | bool):
                return 0 if result else 1
            else:
                return 0

        except CalculationError as e:
            self.console.print(f"[red]expr: {e}[/red]")
            return 2
        except Exception as e:
            self.console.print(f"[red]expr: {e}[/red]")
            return 2

    def _evaluate_expression(self, tokens: list[str]) -> int | float | str | bool:
        """Evaluate an expression from tokens."""
        if not tokens:
            raise CalculationError("empty expression")

        # Handle special functions first:
        if len(tokens) >= 2 and tokens[0] == "length":
            return len(tokens[1])

        if len(tokens) >= 4 and tokens[0] == "substr":
            string = tokens[1]
            try:
                start = int(tokens[2]) - 1  # expr uses 1-based indexing
                length = int(tokens[3])
                return string[start : start + length]
            except (ValueError, IndexError) as e:
                raise CalculationError("invalid substr arguments") from e

        return self._parse_or_expression(tokens, 0)[0]

    def _parse_or_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse OR expression (lowest precedence)."""
        left, pos = self._parse_and_expression(tokens, pos)

        while pos < len(tokens) and tokens[pos] == "|":
            pos += 1  # Skip "|"
            right, pos = self._parse_and_expression(tokens, pos)
            left = self._to_bool(left) or self._to_bool(right)

        return left, pos

    def _parse_and_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse AND expression."""
        left, pos = self._parse_relational_expression(tokens, pos)

        while pos < len(tokens) and tokens[pos] == "&":
            pos += 1  # Skip "&"
            right, pos = self._parse_relational_expression(tokens, pos)
            left = self._to_bool(left) and self._to_bool(right)

        return left, pos

    def _parse_relational_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse relational expression."""
        left, pos = self._parse_additive_expression(tokens, pos)

        if pos < len(tokens) and tokens[pos] in ["<", "<=", "=", "!=", ">=", ">"]:
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_additive_expression(tokens, pos)

            # Convert to numbers if possible.
            left_num = self._try_to_number(left)
            right_num = self._try_to_number(right)

            if isinstance(left_num, int | float) and isinstance(right_num, int | float):
                if op == "<":
                    left = left_num < right_num
                elif op == "<=":
                    left = left_num <= right_num
                elif op == "=":
                    left = left_num == right_num
                elif op == "!=":
                    left = left_num != right_num
                elif op == ">=":
                    left = left_num >= right_num
                elif op == ">":
                    left = left_num > right_num
            else:
                # String comparison.
                left_str = str(left)
                right_str = str(right)
                if op == "<":
                    left = left_str < right_str
                elif op == "<=":
                    left = left_str <= right_str
                elif op == "=":
                    left = left_str == right_str
                elif op == "!=":
                    left = left_str != right_str
                elif op == ">=":
                    left = left_str >= right_str
                elif op == ">":
                    left = left_str > right_str

        return left, pos

    def _parse_additive_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse additive expression."""
        left, pos = self._parse_multiplicative_expression(tokens, pos)

        while pos < len(tokens) and tokens[pos] in ["+", "-"]:
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_multiplicative_expression(tokens, pos)

            left_num = self._try_to_number(left)
            right_num = self._try_to_number(right)

            if isinstance(left_num, int | float) and isinstance(right_num, int | float):
                if op == "+":
                    left = left_num + right_num
                elif op == "-":
                    left = left_num - right_num
            else:
                raise CalculationError(f"non-numeric argument to {op}")

        return left, pos

    def _parse_multiplicative_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse multiplicative expression."""
        left, pos = self._parse_match_expression(tokens, pos)

        while pos < len(tokens) and tokens[pos] in ["*", "/", "%"]:
            op = tokens[pos]
            pos += 1
            right, pos = self._parse_match_expression(tokens, pos)

            left_num = self._try_to_number(left)
            right_num = self._try_to_number(right)

            if isinstance(left_num, int | float) and isinstance(right_num, int | float):
                if op == "*":
                    left = left_num * right_num
                elif op == "/":
                    if right_num == 0:
                        raise CalculationError("division by zero")
                    left = int(left_num // right_num)  # Integer division like expr
                elif op == "%":
                    if right_num == 0:
                        raise CalculationError("division by zero")
                    left = left_num % right_num
            else:
                raise CalculationError(f"non-numeric argument to {op}")

        return left, pos

    def _parse_match_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse match expression."""
        left, pos = self._parse_primary_expression(tokens, pos)

        if pos < len(tokens) and tokens[pos] == ":":
            pos += 1  # Skip ":"
            right, pos = self._parse_primary_expression(tokens, pos)

            # String matching.
            string = str(left)
            pattern = str(right)

            try:
                match = re.search(pattern, string)
                left = len(match.group(0)) if match else 0
            except re.error as e:
                raise CalculationError("invalid regular expression") from e

        return left, pos

    def _parse_primary_expression(
        self, tokens: list[str], pos: int
    ) -> tuple[int | float | str | bool, int]:
        """Parse primary expression."""
        if pos >= len(tokens):
            raise CalculationError("unexpected end of expression")

        token = tokens[pos]
        pos += 1

        number = self._try_to_number(token)
        if isinstance(number, int | float):
            return number, pos

        # Return as string:
        return token, pos

    def _try_to_number(
        self, value: str | int | float | bool
    ) -> int | float | str | bool:
        """Try to convert value to number."""
        if isinstance(value, int | float):
            return value
        if isinstance(value, bool):
            return value

        try:
            if "." in str(value):
                return float(value)
            else:
                return int(value)
        except (ValueError, TypeError):
            return value

    def _to_bool(self, value: int | float | str | bool) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, int | float):
            return value != 0
        if isinstance(value, str):
            return value != ""
        return False
