"""Implementation of DcCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, parse_flags, safe_read_file
from .._base import Command
from .exceptions import CalculationError

if TYPE_CHECKING:
    import shimmer


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DcCommand(Command):
    """Implementation of dc (desk calculator) command."""

    name = "dc"
    help = "Reverse-polish desk calculator"
    category = "Mathematical Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Reverse-polish desk calculator.

Usage: dc [OPTIONS] [FILE...]

Description:
    dc is a reverse-polish desk calculator which supports unlimited
    precision arithmetic. It reads from standard input or files.

Options:
    -e EXPR         Evaluate expression
    -f FILE         Read from file
    -h, --help      Show this help message

Operations:
    +, -, *, /      Basic arithmetic
    %               Modulo
    ^               Exponentiation
    p               Print top of stack
    f               Print entire stack
    d               Duplicate top of stack
    c               Clear stack
    q               Quit

Numbers:
    Simply enter numbers to push them onto the stack

Examples:
    dc -e '2 3 + p'     # Push 2, push 3, add, print (outputs 5)
    dc -e '10 3 / p'    # Push 10, push 3, divide, print
    dc -e '2 3 ^ p'     # Push 2, push 3, exponentiate, print (outputs 8)
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dc command."""
        if handle_help_flag(self, args):
            return 0

        parse_result = parse_flags(
            args,
            {
                "e": str,  # expression
                "f": str,  # file
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        expression = flags.get("e")
        input_file = flags.get("f")

        try:
            if expression:
                return self._execute_expression(expression)
            elif input_file:
                content = safe_read_file(client, input_file, self.shell)
                if content is None:
                    return 1
                return self._execute_expression(content)
            elif positional_args:
                for file_path in positional_args:
                    content = safe_read_file(client, file_path, self.shell)
                    if content is None:
                        continue
                    result = self._execute_expression(content)
                    if result != 0:
                        return result
                return 0
            else:
                # TODO: We could add this in the future.
                self.console.print(
                    "[yellow]dc: interactive mode not supported[/yellow]"
                )
                return 1

        except ops.pebble.PathError as e:
            self.console.print(f"[red]dc: {e}[/red]")
            return 1
        except CalculationError as e:
            self.console.print(f"[red]dc: {e}[/red]")
            return 1
        except Exception as e:
            self.console.print(f"[red]dc: {e}[/red]")
            return 1

    def _execute_expression(self, expression: str) -> int:
        """Execute a dc expression."""
        stack = []
        tokens = expression.split()

        for token in tokens:
            try:
                if token.replace(".", "").replace("-", "").isdigit():
                    if "." in token:
                        stack.append(float(token))
                    else:
                        stack.append(int(token))
                elif token == "+":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    stack.append(a + b)
                elif token == "-":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    stack.append(a - b)
                elif token == "*":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    stack.append(a * b)
                elif token == "/":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    if b == 0:
                        raise CalculationError("division by zero")
                    stack.append(a / b)
                elif token == "%":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    if b == 0:
                        raise CalculationError("division by zero")
                    stack.append(a % b)
                elif token == "^":  # noqa: S105
                    if len(stack) < 2:
                        raise CalculationError("stack underflow")
                    b = stack.pop()
                    a = stack.pop()
                    stack.append(a**b)
                elif token == "p":  # noqa: S105
                    # Print top of stack
                    if not stack:
                        raise CalculationError("stack empty")
                    result = stack[-1]
                    if isinstance(result, float) and result.is_integer():
                        self.console.print(str(int(result)))
                    else:
                        self.console.print(str(result))
                elif token == "f":  # noqa: S105
                    # Print entire stack
                    for item in reversed(stack):
                        if isinstance(item, float) and item.is_integer():
                            self.console.print(str(int(item)))
                        else:
                            self.console.print(str(item))
                elif token == "d":  # noqa: S105
                    # Duplicate top of stack
                    if not stack:
                        raise CalculationError("stack empty")
                    stack.append(stack[-1])
                elif token == "c":  # noqa: S105
                    # Clear stack
                    stack.clear()
                elif token == "q":  # noqa: S105
                    # Quit
                    break
                else:
                    raise CalculationError(f"unknown operation: {token}")

            except (ValueError, OverflowError) as e:
                raise CalculationError(f"calculation error: {e}") from e

        return 0
