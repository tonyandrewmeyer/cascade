# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cascade (`pebble-cascade`) is a Python shell for debugging containers — particularly bare rocks — using Pebble's filesystem operations. It provides 170+ shell commands (ls, cat, grep, ps, etc.) that work without requiring a shell on the remote container. It connects via direct Pebble socket or Juju SSH.

Package name: `pebble-cascade`. Source package: `src/pebble_shell/`.

## Common Commands

```bash
# Install dependencies
uv sync

# Run the shell
uv run cascade

# Run all tests (coverage is on by default via pyproject.toml addopts)
uv run pytest

# Run a single test file or test
uv run pytest tests/unit/test_utils/test_parser.py
uv run pytest tests/unit/test_utils/test_parser.py::TestShellParser::test_parse_simple_command

# Run integration tests (requires a Pebble server)
uv run pytest tests/integration/

# Lint (ruff check + ruff format check + ty type check)
tox -e lint

# Auto-format
tox -e format

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## Architecture

### Core Flow

User input enters `PebbleShell` (shell.py) which manages the interactive loop, readline, aliases, and variables. Input is parsed by `ShellParser` (utils/parser.py) which handles tokenization, variable expansion (`$VAR`), glob expansion, quoting, and shell syntax (pipes, redirection, chaining). Parsed commands go to `PipelineExecutor` (utils/executor.py) which handles pipes (`|`), redirection (`>`, `>>`), command chaining (`&&`, `||`, `;`), and for-loops.

### Command System

Commands use a **metaclass-based auto-registration** pattern. All commands inherit from `Command` (commands/_base.py) and are automatically registered by `CommandMeta` when their module is imported. To add a new command:

1. Create a file in the appropriate `src/pebble_shell/commands/<category>/` directory
2. Subclass `Command` with required class attributes: `name`, `help`, `category`
3. Implement `execute(self, client, args) -> int` (return 0 for success)
4. Import the new command class in the category's `__init__.py`
5. Import and export it in `commands/__init__.py`

The `commands/__init__.py` has explicit imports for all command classes (not just the category modules) — both forms of import are required due to test compatibility issues.

### Dual Client Support

Commands receive either `ops.pebble.Client` (direct socket) or `shimmer.PebbleCliClient` (CLI-based via Juju SSH). Use the union type `ops.pebble.Client | shimmer.PebbleCliClient` in signatures.

### Key Utilities

- **command_helpers.py**: Flag parsing (`parse_flags`), glob expansion for file args, path resolution, progress bars
- **proc_reader.py**: Reads `/proc` filesystem for process/system info
- **theme.py**: Rich console styling; all output uses Rich library
- **pathutils.py**: Path resolution with tilde expansion and relative path support

## Code Conventions

- **Python 3.11+** required (despite some broader classifiers in pyproject.toml)
- **Ruff** for linting and formatting (line length 88, Google-style docstrings)
- **ty** for type checking (used in pre-commit and tox lint)
- **`from __future__ import annotations`** used throughout
- **`TYPE_CHECKING`** guard for conditional imports of `ops`, `shimmer`, and internal types
- Errors displayed via Rich `Panel` widgets using `format_error()` or `theme.error_text()`
- Commands return `int` exit codes (0 = success); exit code accessible via `$?`
- Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`, `@pytest.mark.pebble`
- Integration tests auto-skip when no Pebble server is available
