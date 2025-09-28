"""DD command for Cascade."""

from __future__ import annotations

import math
from io import BytesIO
from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import handle_help_flag, safe_read_file
from ...utils.theme import get_theme
from .._base import Command

if TYPE_CHECKING:
    import shimmer



# TODO: Use the prototype from Shimmer.
ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]


class DdCommand(Command):
    """Implementation of dd command."""

    name = "dd"
    help = "Convert and copy a file"
    category = "Data Processing"

    def show_help(self):
        """Show command help."""
        help_text = """Convert and copy a file.

Usage: dd [OPERAND]...

Description:
    Copy a file, converting and formatting according to the operands.

Operands:
    if=FILE         Read from FILE instead of stdin
    of=FILE         Write to FILE instead of stdout
    bs=BYTES        Read and write BYTES bytes at a time
    ibs=BYTES       Read BYTES bytes at a time (default: 512)
    obs=BYTES       Write BYTES bytes at a time (default: 512)
    count=N         Copy only N input blocks
    skip=N          Skip N ibs-sized blocks at start of input
    seek=N          Skip N obs-sized blocks at start of output
    conv=CONVS      Convert the file as per the comma separated symbol list

Conversions:
    ascii           Convert EBCDIC to ASCII
    ebcdic          Convert ASCII to EBCDIC
    lcase           Change uppercase to lowercase
    ucase           Change lowercase to uppercase
    nocreat         Do not create the output file
    notrunc         Do not truncate the output file
    sync            Pad every input block with NULs to ibs-size

Options:
    -h, --help      Show this help message

Examples:
    dd if=/dev/zero of=output.txt bs=1024 count=10
    dd if=input.txt of=output.txt conv=ucase
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the dd command."""
        if handle_help_flag(self, args):
            return 0

        # Parse dd operands (key=value format).
        # TODO: Can this use common flag parsing code?
        operands = {}
        for arg in args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                operands[key] = value
            else:
                self.console.print(
                    get_theme().error_text(f"dd: invalid operand '{arg}'")
                )
                return 1

        # Default values
        input_file = operands.get("if")
        output_file = operands.get("of")
        block_size = self._parse_size(operands.get("bs"))
        input_block_size = self._parse_size(operands.get("ibs", "512"))
        output_block_size = self._parse_size(operands.get("obs", "512"))
        count = int(operands.get("count", -1)) if operands.get("count") else -1
        skip = int(operands.get("skip", 0)) if operands.get("skip") else 0
        seek = int(operands.get("seek", 0)) if operands.get("seek") else 0
        conversions = (
            operands.get("conv", "").split(",") if operands.get("conv") else []
        )

        # Use block_size if specified, otherwise use separate ibs/obs
        if block_size:
            input_block_size = output_block_size = block_size

        try:
            # Read input data
            if input_file:
                input_data = safe_read_file(client, input_file, self.shell)
                if input_data is None:
                    self.console.print(
                        get_theme().error_text(
                            f"dd: {input_file}: No such file or directory"
                        )
                    )
                    return 1
            else:
                # TODO: Handle stdin
                self.console.print(
                    get_theme().warning_text("dd: reading from stdin not supported")
                )
                return 1

            # Apply skip
            if skip > 0:
                skip_bytes = skip * input_block_size
                input_data = input_data[skip_bytes:]

            # Apply count limit
            if count > 0:
                max_bytes = count * input_block_size
                input_data = input_data[:max_bytes]

            # Apply conversions
            output_data = self._apply_conversions(input_data, conversions)

            # Write output
            if output_file:
                # Apply seek for output
                if seek > 0:
                    # For simplicity, we'll just truncate or create new file
                    # Real dd would seek into existing file
                    pass

                try:
                    output_stream = BytesIO(output_data)
                    client.push(output_file, output_stream)
                except Exception as e:
                    self.console.print(
                        get_theme().error_text(f"dd: {output_file}: {e}")
                    )
                    return 1
            else:
                # Output to stdout (convert to text for display)
                try:
                    text_output = output_data.decode("utf-8", errors="replace")
                    self.console.print(text_output, end="")
                except Exception:
                    # If can't decode, show hex representation
                    hex_output = output_data.hex()
                    self.console.print(f"[hex]{hex_output}[/hex]")

            # Print statistics
            blocks_read = (
                math.ceil(len(input_data) / input_block_size) if input_data else 0
            )
            blocks_written = (
                math.ceil(len(output_data) / output_block_size) if output_data else 0
            )
            self.console.print(
                f"{blocks_read} blocks read", file=self.shell.console.file
            )
            self.console.print(
                f"{blocks_written} blocks written", file=self.shell.console.file
            )

            return 0

        except Exception as e:
            self.console.print(get_theme().error_text(f"dd: {e}"))
            return 1

    def _parse_size(self, size_str: str | None) -> int:
        """Parse size string (e.g., '1024', '1K', '1M')."""
        if not size_str:
            return 512

        size_str = size_str.upper()
        multipliers = {
            "B": 1,
            "K": 1024,
            "M": 1024 * 1024,
            "G": 1024 * 1024 * 1024,
        }

        if size_str[-1] in multipliers:
            return int(size_str[:-1]) * multipliers[size_str[-1]]
        else:
            return int(size_str)

    def _apply_conversions(self, data: bytes, conversions: list[str]) -> bytes:
        """Apply conversion operations to data."""
        result = bytearray(data)

        for conv in conversions:
            conv = conv.strip()
            if conv == "lcase":
                result = bytearray(b + 32 if 65 <= b <= 90 else b for b in result)
            elif conv == "ucase":
                result = bytearray(b - 32 if 97 <= b <= 122 else b for b in result)
            elif conv == "ascii":
                # Simple EBCDIC to ASCII (simplified)
                pass  # Would need EBCDIC translation table
            elif conv == "sync":
                # Pad to block boundary with nulls
                pass  # Would need block size context

        return bytes(result)
