# Clipboard Commands Implementation Plan

This document outlines the plan for implementing clipboard commands in Cascade.

## Overview

Implement clipboard commands (`copy`, `pasta`, `pastas`, `cpwd`) that interact with the **local** clipboard while operating within the Cascade shell. This allows users to copy data from container inspection to their local clipboard and paste local clipboard content into commands.

## Dependency Choice: `pyperclip`

We'll use [pyperclip](https://pypi.org/project/pyperclip/) as the clipboard library:

- **Cross-platform**: Works on Windows, macOS, and Linux
- **Well-maintained**: Active development, widely used
- **Simple API**: Just `pyperclip.copy()` and `pyperclip.paste()`
- **Lightweight**: No heavy dependencies

### Alternative Considered
- `pyclip` - Similar functionality but less popular
- `clipboard` - Wrapper around pyperclip, unnecessary indirection

## Installation Approach

### Optional Dependency
Add `pyperclip` as an optional dependency in `pyproject.toml`:

```toml
[project.optional-dependencies]
clipboard = ["pyperclip>=1.8.0"]
```

Users install with: `pip install pebble-cascade[clipboard]`

### Graceful Degradation
Commands will check for pyperclip availability and show a helpful error if not installed:

```
clipboard: pyperclip is not installed.
Install it with: pip install pebble-cascade[clipboard]
```

## Commands to Implement

### 1. `copy`
**Purpose**: Copy stdin or arguments to clipboard

```bash
# Copy command output
cat /etc/os-release | copy

# Copy text directly
copy "some text to copy"

# Copy from file
cat config.yaml | copy
```

### 2. `pasta` (paste)
**Purpose**: Output clipboard contents to stdout

```bash
# Print clipboard contents
pasta

# Pipe clipboard to another command
pasta | grep pattern

# Save clipboard to file (via shell redirection)
# Note: Would need shell pipe support
```

### 3. `cpwd`
**Purpose**: Copy current working directory to clipboard

```bash
# Copy current directory path
cpwd
# Output: Copied: /var/log
```

### 4. `pastas` (clipboard monitor)
**Purpose**: Monitor clipboard and print changes

**Note**: This command requires continuous execution and may not fit well with Cascade's command model. We'll implement a simplified version that shows current content and optionally watches for a limited time.

```bash
# Show current clipboard and watch for changes (with timeout)
pastas -t 30  # Watch for 30 seconds
```

## Implementation Details

### Utility Module
Create a utility module for clipboard operations at:
`src/pebble_shell/utils/clipboard.py`

```python
"""Clipboard utilities with graceful degradation."""

CLIPBOARD_AVAILABLE = False
CLIPBOARD_ERROR = ""

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_ERROR = (
        "pyperclip is not installed.\n"
        "Install it with: pip install pebble-cascade[clipboard]"
    )

def copy_to_clipboard(text: str) -> None:
    """Copy text to clipboard."""
    if not CLIPBOARD_AVAILABLE:
        raise ImportError(CLIPBOARD_ERROR)
    pyperclip.copy(text)

def paste_from_clipboard() -> str:
    """Get text from clipboard."""
    if not CLIPBOARD_AVAILABLE:
        raise ImportError(CLIPBOARD_ERROR)
    return pyperclip.paste()
```

### Command Location
Place commands in: `src/pebble_shell/commands/clipboard/`

### Category
Commands will use category: `"Clipboard"`

## File Structure

```
src/pebble_shell/
├── utils/
│   └── clipboard.py          # Clipboard utility functions
└── commands/
    └── clipboard/
        ├── __init__.py
        ├── copy.py            # copy command
        ├── pasta.py           # pasta command
        ├── cpwd.py            # cpwd command
        └── pastas.py          # pastas command (optional)
```

## Error Handling

When pyperclip is not installed:
```
[red]copy: clipboard support not available[/red]
[yellow]Install with: pip install pebble-cascade[clipboard][/yellow]
```

When clipboard access fails (e.g., no display on Linux):
```
[red]copy: failed to access clipboard: <error message>[/red]
[yellow]On Linux, ensure xclip or xsel is installed.[/yellow]
```

## Testing Notes

- Test with pyperclip installed and not installed
- Test clipboard error handling (e.g., headless Linux)
- Mock pyperclip for unit tests

## Implementation Order

1. Add `pyperclip` optional dependency to `pyproject.toml`
2. Create `clipboard.py` utility module
3. Create `clipboard/` command directory with `__init__.py`
4. Implement `copy` command
5. Implement `pasta` command
6. Implement `cpwd` command
7. Implement `pastas` command (simplified version)
8. Commit and test
