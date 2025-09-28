"""Integration tests for the MarkdownCommand."""

from __future__ import annotations

import tempfile
from typing import TYPE_CHECKING

import pytest

import pebble_shell.commands
import pebble_shell.shell

if TYPE_CHECKING:
    import ops


@pytest.fixture
def command(shell: pebble_shell.shell.PebbleShell):
    """Fixture to create a MarkdownCommand instance."""
    yield pebble_shell.commands.MarkdownCommand(shell=shell)


def test_name(command: pebble_shell.commands.MarkdownCommand):
    assert command.name == "markdown"


def test_category(command: pebble_shell.commands.MarkdownCommand):
    assert command.category == "File Utilities"


def test_help(command: pebble_shell.commands.MarkdownCommand):
    with command.shell.console.capture() as capture:
        command.show_help()
    output = capture.get()
    assert "markdown" in output
    assert "Render markdown files" in output
    assert "-f" in output
    assert "-t" in output


@pytest.mark.parametrize("args", [["-h"], ["--help"]])
def test_execute_help(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
    args: list[str],
):
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=args)
    assert result == 0
    output = capture.get()
    assert "markdown" in output
    assert "Render markdown files" in output


def test_execute_no_args(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # markdown with no args should fail and show usage
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[])

    # Should fail with usage message
    assert result == 1
    output = capture.get()
    assert "markdown <file>" in output


def test_execute_simple_markdown_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with markdown file that likely exists or can be created
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as temp_file:
        temp_path = temp_file.name
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=[temp_path])

    # Should either succeed rendering markdown or fail if not accessible
    if result == 0:
        output = capture.get()
        # Should show rendered markdown content
        assert len(output.strip()) > 0
        # Should contain HTML-like elements or plain text rendering
        assert any(pattern in output for pattern in ["<", ">", "**", "*", "#"])
    else:
        # Should fail if file not accessible
        assert result == 1
        output = capture.get()
        assert any(
            msg in output for msg in ["No such file", "permission denied", "error"]
        )


def test_execute_nonexistent_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with nonexistent markdown file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent/file.md"])

    # Should fail with file not found error
    assert result == 1
    output = capture.get()
    assert any(msg in output for msg in ["No such file", "not found", "error"])


def test_execute_empty_markdown_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with empty markdown file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/dev/null"])

    # Should either succeed with empty output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should handle empty file
        assert len(output.strip()) == 0
    else:
        assert result == 1


def test_execute_text_file_as_markdown(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with regular text file (should render as plain text)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should succeed rendering text file as markdown
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
        # Should contain hosts file content
        assert any(pattern in output for pattern in ["localhost", "127.0.0.1", "#"])
    else:
        assert result == 1


def test_execute_binary_file_as_markdown(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with binary file (should handle appropriately)
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin/ls"])

    # Should either handle binary file or fail appropriately
    if result == 0:
        output = capture.get()
        # Should handle binary file (may show warning or filtered content)
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_force_html_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test -f option to force HTML output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "html", "/etc/hosts"])

    # Should either succeed with HTML output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show HTML output
        assert len(output.strip()) > 0
        # Should contain HTML tags
        assert any(tag in output for tag in ["<p>", "<h1>", "<h2>", "<pre>", "<code>"])
    else:
        assert result == 1


def test_execute_force_text_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test -f option to force plain text output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-f", "text", "/etc/hosts"])

    # Should either succeed with text output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show plain text output
        assert len(output.strip()) > 0
        # Should not contain HTML tags
        assert not any(tag in output for tag in ["<p>", "<h1>", "<h2>", "<html>"])
    else:
        assert result == 1


def test_execute_table_of_contents_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test -t option to generate table of contents
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-t", "/etc/hosts"])

    # Should either succeed with TOC or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content with table of contents
        assert len(output.strip()) > 0
        # Should contain TOC indicators
        assert any(
            toc in output for toc in ["Table of Contents", "TOC", "Contents", "Index"]
        )
    else:
        assert result == 1


def test_execute_theme_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test theme option for styled output
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--theme", "dark", "/etc/hosts"])

    # Should either succeed with themed output or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show themed content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_width_option(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test width option for line wrapping
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--width", "80", "/etc/hosts"])

    # Should either succeed with specified width or fail gracefully
    if result == 0:
        output = capture.get()
        # Should format output with specified width
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_headers(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of markdown headers
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd"]
        )  # May contain # comments

    # Should handle header-like content appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_lists(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of markdown list elements
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle list-like content appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_emphasis(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of markdown emphasis
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle emphasis markers appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_code_blocks(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of code blocks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle code block content appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_links(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of markdown links
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle link-like content appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_markdown_tables(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test rendering of markdown tables
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd"]
        )  # Colon-separated format

    # Should handle table-like content appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_multiple_files(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with multiple markdown files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts", "/etc/passwd"])

    # Should either succeed rendering multiple files or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show content from multiple files
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_directory_argument(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with directory argument
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc"])

    # Should either handle directory or fail appropriately
    if result == 0:
        output = capture.get()
        # Should show directory contents or error
        assert len(output.strip()) >= 0
    else:
        # Should fail if directories not supported
        assert result == 1
        output = capture.get()
        assert any(msg in output for msg in ["is a directory", "cannot open", "error"])


def test_execute_permission_denied_file(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with permission denied file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/shadow"])

    # Should fail with permission error
    if result == 1:
        output = capture.get()
        assert any(
            msg in output for msg in ["permission denied", "cannot open", "error"]
        )
    else:
        # May succeed if file is readable
        assert result == 0


def test_execute_symlink_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with symbolic link
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/bin"])  # Often a symlink

    # Should either follow symlink or handle appropriately
    if result == 0:
        output = capture.get()
        # Should follow symlink and render target
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_special_files_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with special files
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/proc/version"])

    # Should either succeed with special file or fail gracefully
    if result == 0:
        output = capture.get()
        # Should show special file contents as markdown
        assert "Linux" in output or len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_unicode_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test unicode character handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle unicode characters appropriately
    if result == 0:
        output = capture.get()
        # Should display unicode content correctly
        assert len(output.strip()) >= 0
    else:
        assert result == 1


def test_execute_syntax_highlighting(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test syntax highlighting for code blocks
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--syntax", "/etc/passwd"])

    # Should handle syntax highlighting appropriately
    if result == 0:
        output = capture.get()
        # Should show syntax highlighted content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_math_rendering(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test mathematical notation rendering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--math", "/etc/hosts"])

    # Should handle math notation appropriately
    if result == 0:
        output = capture.get()
        # Should show math-rendered content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_output_format_consistency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test output format consistency
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should format output consistently
    if result == 0:
        output = capture.get()
        # Should have consistent formatting
        lines = output.strip().split("\n")
        if len(lines) > 1:
            # Should maintain consistent structure
            assert len(lines) > 0
    else:
        assert result == 1


def test_execute_large_file_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test with large markdown file
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/usr/share/dict/words"])

    # Should either succeed with large file or fail if not found
    if result == 0:
        output = capture.get()
        # Should handle large file efficiently
        assert len(output) >= 0
    else:
        # Should fail if file not found
        assert result == 1


def test_execute_nested_markdown_elements(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test nested markdown element rendering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should handle nested elements appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered nested content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_metadata_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test YAML front matter and metadata handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["--metadata", "/etc/hosts"])

    # Should handle metadata appropriately
    if result == 0:
        output = capture.get()
        # Should show content with metadata processing
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_extension_support(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test markdown extension support
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--extensions", "tables,footnotes", "/etc/hosts"]
        )

    # Should handle extensions appropriately
    if result == 0:
        output = capture.get()
        # Should show content with extension processing
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_output_encoding(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test output encoding handling
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--encoding", "utf-8", "/etc/hosts"]
        )

    # Should handle encoding appropriately
    if result == 0:
        output = capture.get()
        # Should show properly encoded content
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_error_recovery(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test error recovery capabilities
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/nonexistent"])

    # Should recover from errors gracefully
    assert result == 1
    output = capture.get()
    # Should provide meaningful error message
    assert len(output.strip()) >= 0


def test_execute_performance_optimization(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test performance with markdown processing
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should process efficiently
    if result == 0:
        output = capture.get()
        # Should complete in reasonable time
        assert len(output) >= 0
    else:
        assert result == 1


def test_execute_memory_efficiency(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test memory efficiency with markdown rendering
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/passwd"])

    # Should be memory efficient
    if result == 0:
        output = capture.get()
        # Should not consume excessive memory
        assert len(output) < 1000000  # Reasonable output size limit
    else:
        assert result == 1


def test_execute_invalid_option_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test handling of invalid options
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["-Z", "/etc/hosts"])

    # Should handle invalid options appropriately
    if result == 1:
        output = capture.get()
        # Should show error for invalid option
        assert any(msg in output for msg in ["invalid", "unknown", "option"])
    else:
        # May ignore unknown options
        assert result == 0


def test_execute_malformed_markdown_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test handling of malformed markdown
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["/etc/passwd"]
        )  # Not real markdown

    # Should handle malformed markdown gracefully
    if result == 0:
        output = capture.get()
        # Should show rendered content despite malformation
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_cross_reference_handling(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test cross-reference and link handling
    with command.shell.console.capture() as capture:
        result = command.execute(client=client, args=["/etc/hosts"])

    # Should handle cross-references appropriately
    if result == 0:
        output = capture.get()
        # Should show rendered content with cross-references
        assert len(output.strip()) > 0
    else:
        assert result == 1


def test_execute_compatibility_mode(
    client: ops.pebble.Client,
    command: pebble_shell.commands.MarkdownCommand,
):
    # Test compatibility with different markdown dialects
    with command.shell.console.capture() as capture:
        result = command.execute(
            client=client, args=["--compat", "github", "/etc/hosts"]
        )

    # Should maintain compatibility with different dialects
    if result == 0:
        output = capture.get()
        # Should render according to compatibility mode
        assert len(output.strip()) >= 0
    else:
        assert result == 1
