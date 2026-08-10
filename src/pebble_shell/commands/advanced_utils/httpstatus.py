"""HTTP status code command for Cascade.

This module provides implementation for the httpstatus command that displays
HTTP status code descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

import ops

from ...utils.command_helpers import parse_flags
from .._base import Command

if TYPE_CHECKING:
    import shimmer

ClientType = Union[ops.pebble.Client, "shimmer.PebbleCliClient"]

# HTTP status codes and their descriptions
HTTP_STATUS_CODES = {
    # 1xx Informational
    100: ("Continue", "The server has received the request headers and the client should proceed to send the request body."),
    101: ("Switching Protocols", "The requester has asked the server to switch protocols and the server has agreed."),
    102: ("Processing", "The server has received and is processing the request, but no response is available yet."),
    103: ("Early Hints", "Used to return some response headers before final HTTP message."),

    # 2xx Success
    200: ("OK", "The request has succeeded."),
    201: ("Created", "The request has been fulfilled and a new resource has been created."),
    202: ("Accepted", "The request has been accepted for processing, but processing has not been completed."),
    203: ("Non-Authoritative Information", "The returned information is from a cached copy."),
    204: ("No Content", "The server successfully processed the request but is not returning any content."),
    205: ("Reset Content", "The server successfully processed the request but is not returning any content. The client should reset the document view."),
    206: ("Partial Content", "The server is delivering only part of the resource due to a range header sent by the client."),
    207: ("Multi-Status", "The message body contains multiple status codes for multiple independent operations."),
    208: ("Already Reported", "The members of a DAV binding have already been enumerated."),
    226: ("IM Used", "The server has fulfilled a request for the resource, and the response is a representation of the result."),

    # 3xx Redirection
    300: ("Multiple Choices", "There are multiple options for the resource that the client may follow."),
    301: ("Moved Permanently", "The resource has been moved permanently to a new URL."),
    302: ("Found", "The resource resides temporarily under a different URL."),
    303: ("See Other", "The response can be found under a different URL using a GET method."),
    304: ("Not Modified", "The resource has not been modified since the last request."),
    305: ("Use Proxy", "The requested resource must be accessed through a proxy."),
    307: ("Temporary Redirect", "The request should be repeated with another URL, but future requests should still use the original URL."),
    308: ("Permanent Redirect", "The request and all future requests should be repeated using another URL."),

    # 4xx Client Errors
    400: ("Bad Request", "The server cannot process the request due to a client error."),
    401: ("Unauthorized", "Authentication is required and has failed or has not been provided."),
    402: ("Payment Required", "Reserved for future use."),
    403: ("Forbidden", "The server understood the request but refuses to authorize it."),
    404: ("Not Found", "The requested resource could not be found."),
    405: ("Method Not Allowed", "The request method is not supported for the requested resource."),
    406: ("Not Acceptable", "The requested resource cannot generate acceptable content."),
    407: ("Proxy Authentication Required", "The client must first authenticate itself with the proxy."),
    408: ("Request Timeout", "The server timed out waiting for the request."),
    409: ("Conflict", "The request could not be processed because of conflict in the request."),
    410: ("Gone", "The resource requested is no longer available and will not be available again."),
    411: ("Length Required", "The request did not specify the length of its content."),
    412: ("Precondition Failed", "The server does not meet one of the preconditions in the request."),
    413: ("Payload Too Large", "The request is larger than the server is willing or able to process."),
    414: ("URI Too Long", "The URI provided was too long for the server to process."),
    415: ("Unsupported Media Type", "The request entity has a media type which the server does not support."),
    416: ("Range Not Satisfiable", "The client has asked for a portion of the file the server cannot supply."),
    417: ("Expectation Failed", "The server cannot meet the requirements of the Expect request-header field."),
    418: ("I'm a teapot", "The server refuses to brew coffee because it is a teapot (RFC 2324)."),
    421: ("Misdirected Request", "The request was directed at a server that cannot produce a response."),
    422: ("Unprocessable Entity", "The request was well-formed but could not be followed due to semantic errors."),
    423: ("Locked", "The resource that is being accessed is locked."),
    424: ("Failed Dependency", "The request failed due to failure of a previous request."),
    425: ("Too Early", "The server is unwilling to risk processing a request that might be replayed."),
    426: ("Upgrade Required", "The client should switch to a different protocol."),
    428: ("Precondition Required", "The origin server requires the request to be conditional."),
    429: ("Too Many Requests", "The user has sent too many requests in a given amount of time."),
    431: ("Request Header Fields Too Large", "The server is unwilling to process the request because its header fields are too large."),
    451: ("Unavailable For Legal Reasons", "The resource is unavailable due to legal demands."),

    # 5xx Server Errors
    500: ("Internal Server Error", "A generic error message when an unexpected condition was encountered."),
    501: ("Not Implemented", "The server does not recognize the request method."),
    502: ("Bad Gateway", "The server was acting as a gateway and received an invalid response."),
    503: ("Service Unavailable", "The server is currently unavailable."),
    504: ("Gateway Timeout", "The server was acting as a gateway and did not receive a timely response."),
    505: ("HTTP Version Not Supported", "The server does not support the HTTP version used in the request."),
    506: ("Variant Also Negotiates", "Transparent content negotiation for the request results in a circular reference."),
    507: ("Insufficient Storage", "The server is unable to store the representation needed to complete the request."),
    508: ("Loop Detected", "The server detected an infinite loop while processing the request."),
    510: ("Not Extended", "Further extensions to the request are required for the server to fulfill it."),
    511: ("Network Authentication Required", "The client needs to authenticate to gain network access."),
}


class HttpstatusCommand(Command):
    """Display HTTP status code descriptions."""

    name = "httpstatus"
    help = "Display HTTP status code descriptions"
    category = "Reference"

    def show_help(self):
        """Show command help."""
        help_text = """Display HTTP status code descriptions.

Usage: httpstatus [OPTIONS] [CODE...]

Options:
    -h, --help      Show this help message
    -a, --all       Show all status codes
    -c, --category  Show codes by category (1xx, 2xx, etc.)

Arguments:
    CODE            One or more HTTP status codes to look up

Examples:
    httpstatus 404          # Look up a specific code
    httpstatus 200 201 404  # Look up multiple codes
    httpstatus -a           # Show all status codes
    httpstatus -c 4         # Show all 4xx codes
        """
        self.console.print(help_text)

    def execute(self, client: ClientType, args: list[str]) -> int:
        """Execute the httpstatus command."""
        result = parse_flags(
            args,
            {
                "h": bool,
                "help": bool,
                "a": bool,
                "all": bool,
                "c": str,
                "category": str,
            },
            self.shell,
        )
        if result is None:
            return 1
        flags, positional_args = result

        if flags["h"] or flags["help"]:
            self.show_help()
            return 0

        if flags["a"] or flags["all"]:
            self._display_all_codes()
            return 0

        category = flags["c"] or flags["category"]
        if category:
            self._display_category(category)
            return 0

        if not positional_args:
            self.show_help()
            return 0

        exit_code = 0
        for code_str in positional_args:
            try:
                code = int(code_str)
                if code in HTTP_STATUS_CODES:
                    name, description = HTTP_STATUS_CODES[code]
                    self.console.print(f"[cyan]{code}[/cyan] [bold]{name}[/bold]")
                    self.console.print(f"  {description}")
                else:
                    self.console.print(f"[yellow]httpstatus: unknown status code: {code}[/yellow]")
                    exit_code = 1
            except ValueError:
                self.console.print(f"[red]httpstatus: invalid status code: {code_str}[/red]")
                exit_code = 1

        return exit_code

    def _display_all_codes(self):
        """Display all HTTP status codes."""
        current_category = None
        for code in sorted(HTTP_STATUS_CODES.keys()):
            category = code // 100
            if category != current_category:
                current_category = category
                category_names = {
                    1: "Informational",
                    2: "Success",
                    3: "Redirection",
                    4: "Client Error",
                    5: "Server Error",
                }
                self.console.print(f"\n[bold magenta]{category}xx {category_names.get(category, 'Unknown')}[/bold magenta]")

            name, _ = HTTP_STATUS_CODES[code]
            self.console.print(f"  [cyan]{code}[/cyan] {name}")

    def _display_category(self, category: str):
        """Display status codes for a specific category."""
        try:
            cat_num = int(category[0])
        except (ValueError, IndexError):
            self.console.print(f"[red]httpstatus: invalid category: {category}[/red]")
            return

        category_names = {
            1: "Informational",
            2: "Success",
            3: "Redirection",
            4: "Client Error",
            5: "Server Error",
        }

        self.console.print(f"[bold magenta]{cat_num}xx {category_names.get(cat_num, 'Unknown')}[/bold magenta]")

        found = False
        for code in sorted(HTTP_STATUS_CODES.keys()):
            if code // 100 == cat_num:
                name, description = HTTP_STATUS_CODES[code]
                self.console.print(f"  [cyan]{code}[/cyan] [bold]{name}[/bold]")
                self.console.print(f"      {description}")
                found = True

        if not found:
            self.console.print(f"[yellow]No status codes found for category {cat_num}xx[/yellow]")
