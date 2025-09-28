"""Implementation of TestCommand."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from .._base import Command

if TYPE_CHECKING:
    import shimmer

    from pebble_shell.shell import PebbleShell


# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class TestCommand(Command):
    """Implementation of test command ([ ])."""

    name = "test"
    help = "Evaluate conditional expressions"
    category = "Advanced Utilities"

    def show_help(self):
        """Show command help."""
        help_text = """Evaluate conditional expressions.

Usage: test EXPRESSION
       [ EXPRESSION ]

Description:
    Evaluate EXPRESSION and return 0 (true) or 1 (false).

File operators:
    -e FILE         File exists
    -f FILE         File is regular file
    -d FILE         File is directory
    -r FILE         File is readable
    -w FILE         File is writable
    -x FILE         File is executable
    -s FILE         File exists and is not empty

String operators:
    -z STRING       String is empty
    -n STRING       String is not empty
    STRING1 = STRING2   Strings are equal
    STRING1 != STRING2  Strings are not equal

Numeric operators:
    INT1 -eq INT2   Integers are equal
    INT1 -ne INT2   Integers are not equal
    INT1 -lt INT2   INT1 is less than INT2
    INT1 -le INT2   INT1 is less than or equal to INT2
    INT1 -gt INT2   INT1 is greater than INT2
    INT1 -ge INT2   INT1 is greater than or equal to INT2

Logical operators:
    ! EXPRESSION    Logical NOT
    EXPR1 -a EXPR2  Logical AND
    EXPR1 -o EXPR2  Logical OR

Examples:
    test -f /etc/passwd
    [ -d /tmp ]
    test "$var" = "value"
    [ $# -gt 0 ]
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the test command."""
        if handle_help_flag(self, args):
            return 0

        if not args:
            # Empty test is false
            return 1

        try:
            result = self._evaluate_expression(client, args)
            return 0 if result else 1
        except Exception as e:
            self.console.print(f"[red]test: {e}[/red]")
            return 2

    def _evaluate_expression(self, client: ClientType, args: list[str]) -> bool:
        """Evaluate a test expression."""
        if not args:
            return False

        # Handle single argument
        if len(args) == 1:
            return bool(args[0])  # Non-empty string is true

        # Handle negation
        if args[0] == "!":
            return not self._evaluate_expression(client, args[1:])

        # Handle binary operators
        if len(args) == 3:
            left, op, right = args

            # File operators
            if op.startswith("-") and len(op) == 2:
                return self._evaluate_file_test(client, op, left)

            # String operators
            if op == "=":
                return left == right
            elif op == "!=":
                return left != right

            # Numeric operators
            try:
                left_num = int(left)
                right_num = int(right)

                numeric_ops = {
                    "-eq": lambda left, right: left == right,
                    "-ne": lambda left, right: left != right,
                    "-lt": lambda left, right: left < right,
                    "-le": lambda left, right: left <= right,
                    "-gt": lambda left, right: left > right,
                    "-ge": lambda left, right: left >= right,
                }
                if op in numeric_ops:
                    return numeric_ops[op](left_num, right_num)
            except ValueError:
                pass

        # Handle unary operators
        if len(args) == 2:
            op, operand = args

            if op == "-z":
                return len(operand) == 0
            elif op == "-n":
                return len(operand) > 0
            elif op.startswith("-") and len(op) == 2:
                return self._evaluate_file_test(client, op, operand)

        # Handle logical operators (simplified)
        if "-a" in args:
            idx = args.index("-a")
            left_expr = args[:idx]
            right_expr = args[idx + 1 :]
            return self._evaluate_expression(
                client, left_expr
            ) and self._evaluate_expression(client, right_expr)

        if "-o" in args:
            idx = args.index("-o")
            left_expr = args[:idx]
            right_expr = args[idx + 1 :]
            return self._evaluate_expression(
                client, left_expr
            ) or self._evaluate_expression(client, right_expr)

        # Default: treat as string test
        return bool(" ".join(args))

    def _evaluate_file_test(self, client: ClientType, op: str, file_path: str) -> bool:
        """Evaluate file test operators."""
        try:
            if op == "-e":
                # File exists
                return safe_read_file(client, file_path, self.shell) is not None

            elif op == "-f":
                # Regular file
                content = safe_read_file(client, file_path, self.shell)
                return content is not None

            elif op == "-d":
                # Directory - check if we can list it
                try:
                    client.list_files(file_path)
                    return True
                except ops.pebble.PathError:
                    return False

            elif op == "-r":
                # Readable
                content = safe_read_file(client, file_path, self.shell)
                return content is not None

            elif op == "-w":
                # Writable (hard to test without actually writing)
                # We'll assume writable if file exists or parent dir exists
                if safe_read_file(client, file_path, self.shell) is not None:
                    return True  # File exists, assume writable
                else:
                    # Check if parent directory exists
                    parent = "/".join(file_path.split("/")[:-1]) or "/"
                    try:
                        client.list_files(parent)
                        return True
                    except ops.pebble.PathError:
                        return False

            elif op == "-x":
                # Executable (approximate check)
                # Check if it's in a typical executable location
                executable_paths = ["/bin/", "/usr/bin/", "/sbin/", "/usr/sbin/"]
                return any(file_path.startswith(path) for path in executable_paths)

            elif op == "-s":
                # Non-empty file
                content = safe_read_file(client, file_path)
                return content is not None and len(content) > 0

        except Exception:
            return False

        return False
