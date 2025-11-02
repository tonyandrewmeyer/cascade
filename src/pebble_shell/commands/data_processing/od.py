"""OD command for Cascade."""

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


class OdCommand(Command):
    """Implementation of od command."""

    name = "od"
    help = "Dump files in octal and other formats"
    category = "Data Processing"

    def show_help(self):
        """Show command help."""
        help_text = """Dump files in octal and other formats.

Usage: od [OPTIONS] [FILE...]

Description:
    Write an unambiguous representation, octal bytes by default,
    of FILE to standard output.

Options:
    -A RADIX        Select address base: o(ctal), d(ecimal), x(hexadecimal), n(one)
    -t TYPE         Select output format(s)
    -N BYTES        Limit dump to BYTES input bytes
    -S BYTES        Skip BYTES input bytes
    -w[BYTES]       Output BYTES bytes per line (default 16)
    -v              Output all data (don't use * for repetition)
    -h, --help      Show this help message

Format types (for -t):
    a               Named characters
    c               ASCII characters or backslash escapes
    d[SIZE]         Signed decimal, SIZE bytes per integer
    f[SIZE]         Floating point, SIZE bytes per float
    o[SIZE]         Octal, SIZE bytes per integer
    u[SIZE]         Unsigned decimal, SIZE bytes per integer
    x[SIZE]         Hexadecimal, SIZE bytes per integer

Examples:
    od file.txt
    od -t x1 file.txt      # Hexadecimal bytes
    od -A x -t x1z file.txt # Hex addresses and bytes with ASCII
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the od command."""
        if handle_help_flag(self, args):
            return 0

        # TODO: Can this use common flag parsing code?
        parse_result = parse_flags(
            args,
            {
                "A": str,  # address radix
                "t": str,  # output format
                "N": str,  # limit bytes
                "S": str,  # skip bytes
                "w": str,  # width
                "v": bool,  # verbose (no *)
            },
            self.shell,
        )
        if parse_result is None:
            return 1
        flags, positional_args = parse_result

        address_radix = flags.get("A", "o")  # octal default
        format_type = flags.get("t") or "o2"  # octal 2-byte default
        limit_bytes = int(flags.get("N", 0)) if flags.get("N") else 0
        skip_bytes = int(flags.get("S", 0)) if flags.get("S") else 0
        width = int(flags.get("w", 16)) if flags.get("w") else 16
        verbose = flags.get("v", False)

        files = positional_args if positional_args else ["-"]
        exit_code = 0

        for file_path in files:
            try:
                if file_path == "-":
                    # TODO: Handle stdin
                    self.console.print(
                        get_theme().warning_text("od: reading from stdin not supported")
                    )
                    continue

                # Read file
                data = safe_read_file(client, file_path, self.shell)
                if data is None:
                    self.console.print(
                        get_theme().error_text(
                            f"od: {file_path}: No such file or directory"
                        )
                    )
                    continue

                # Apply skip
                if skip_bytes > 0:
                    data = data[skip_bytes:]

                # Apply limit
                if limit_bytes > 0:
                    data = data[:limit_bytes]

                # Generate output
                self._dump_data(
                    data, address_radix, format_type, width, verbose, skip_bytes
                )

            except ops.pebble.PathError:
                self.console.print(
                    get_theme().error_text(
                        f"od: {file_path}: No such file or directory"
                    )
                )
                exit_code = 1
            except Exception as e:
                self.console.print(get_theme().error_text(f"od: {file_path}: {e}"))
                exit_code = 1

        return exit_code

    def _dump_data(
        self,
        data: bytes,
        address_radix: str,
        format_type: str,
        width: int,
        verbose: bool,
        offset: int,
    ):
        """Dump binary data in specified format."""
        for i in range(0, len(data), width):
            chunk = data[i : i + width]
            address = offset + i

            # Format address
            if address_radix == "o":
                addr_str = f"{address:07o}"
            elif address_radix == "d":
                addr_str = f"{address:07d}"
            elif address_radix == "x":
                addr_str = f"{address:06x}"
            elif address_radix == "n":
                addr_str = ""
            else:
                addr_str = f"{address:07o}"

            # Format data based on type
            if format_type.startswith("x"):
                # Hexadecimal
                size = int(format_type[1:]) if len(format_type) > 1 else 1
                hex_values = []
                for j in range(0, len(chunk), size):
                    value_bytes = chunk[j : j + size]
                    if len(value_bytes) == size:
                        if size == 1:
                            hex_values.append(f"{value_bytes[0]:02x}")
                        elif size == 2:
                            value = int.from_bytes(value_bytes, byteorder="little")
                            hex_values.append(f"{value:04x}")
                        elif size == 4:
                            value = int.from_bytes(value_bytes, byteorder="little")
                            hex_values.append(f"{value:08x}")

                data_str = " ".join(hex_values)

            elif format_type.startswith("o"):
                # Octal
                size = int(format_type[1:]) if len(format_type) > 1 else 2
                octal_values = []
                for j in range(0, len(chunk), size):
                    value_bytes = chunk[j : j + size]
                    if len(value_bytes) == size:
                        if size == 1:
                            octal_values.append(f"{value_bytes[0]:03o}")
                        elif size == 2:
                            value = int.from_bytes(value_bytes, byteorder="little")
                            octal_values.append(f"{value:06o}")

                data_str = " ".join(octal_values)

            elif format_type == "c":
                # ASCII characters
                char_values = []
                for byte in chunk:
                    if 32 <= byte <= 126:
                        char_values.append(chr(byte))
                    elif byte == 0:
                        char_values.append("\\0")
                    elif byte == 9:
                        char_values.append("\\t")
                    elif byte == 10:
                        char_values.append("\\n")
                    elif byte == 13:
                        char_values.append("\\r")
                    else:
                        char_values.append(f"\\{byte:03o}")

                data_str = " ".join(char_values)

            else:
                # Default to octal bytes
                data_str = " ".join(f"{byte:03o}" for byte in chunk)

            # Print line
            if addr_str:
                self.console.print(f"{addr_str} {data_str}")
            else:
                self.console.print(data_str)
