# Evan Hahn Scripts - Implementation Plan for Cascade

This document analyzes scripts from [Evan Hahn's blog post](https://evanhahn.com/scripts-i-wrote-that-i-use-all-the-time/) and evaluates which ones make sense to implement in Cascade.

## Context: What is Cascade?

Cascade is a Pebble shell for interacting with containers/workloads. It has:
- Filesystem read/write access to containers via Pebble client
- Exec capability for running commands in containers
- Rich terminal output via the Rich library
- Access to the **local** clipboard via optional `pyperclip` dependency
- Ability to open local editors for remote file editing (like `edit` command)

This context is crucial for evaluating which scripts are feasible.

---

## Commands Implemented

These commands have been implemented in Cascade:

### Text Processing

| Command | Description | Category |
|---------|-------------|----------|
| `line` | Extract specific line number from stdin | Text Utilities |
| `straightquote` | Convert smart quotes to straight quotes | Text Utilities |
| `markdownquote` | Add `>` prefix to each line | Text Utilities |
| `length` | Return character count of argument | Text Utilities |
| `jsonformat` | Pretty-print JSON from stdin | Text Utilities |
| `uppered` | Convert string to uppercase | Text Utilities |
| `lowered` | Convert string to lowercase | Text Utilities |
| `nato` | Convert letters to NATO phonetic alphabet | Text Utilities |
| `url` | Parse URL and display components | Text Utilities |
| `u+` | Look up Unicode characters by code point | Text Utilities |

### Date/Time

| Command | Description | Category |
|---------|-------------|----------|
| `hoy` | Print current date in ISO format (YYYY-MM-DD) | System Utilities |
| `rn` | Display current time, date, and calendar | Built-in Commands |

### Reference/Lookup

| Command | Description | Category |
|---------|-------------|----------|
| `httpstatus` | Display HTTP status code descriptions | Reference |
| `alphabet` | Print English alphabet | Reference |

### System/Utilities

| Command | Description | Category |
|---------|-------------|----------|
| `uuid` | Generate v4 UUID | System Utilities |
| `prettypath` | Display PATH with newlines | System Utilities |

### Directory/File Management

| Command | Description | Category |
|---------|-------------|----------|
| `mkcd` | Create directory and cd into it | Built-in Commands |
| `tempe` | Create temp directory and cd into it | Built-in Commands |
| `mksh` | Create executable shell script and edit | Built-in Commands |
| `scratch` | Open scratch buffer and push to remote | Built-in Commands |

### Network

| Command | Description | Category |
|---------|-------------|----------|
| `serveit` | Start simple HTTP server for local files | Built-in Commands |

### Clipboard (Optional Dependency)

Requires: `pip install pebble-cascade[clipboard]`

| Command | Description | Category |
|---------|-------------|----------|
| `copy` | Copy stdin or arguments to clipboard | Clipboard |
| `pasta` | Output clipboard contents to stdout | Clipboard |
| `cpwd` | Copy current working directory to clipboard | Clipboard |
| `pastas` | Monitor clipboard and print changes | Clipboard |

---

## Commands to Skip

### File Management
- `trash` - Moves files to trash instead of deletion

**Reason:** Containers don't have a trash/recycle bin concept. Files should be deleted directly or backed up before removal.

### Audio/Video/Media (No local media access)
- `boop` - Plays success/failure sounds
- `sfx` - Plays sound files
- `tunes` - Audio player
- `pix` - Image viewer
- `radio` - Internet radio
- `speak` - Text-to-speech
- `shrinkvid` - Video compression
- `tuivid` - Terminal video player
- `timer` - Countdown timer with audio alert
- `ocr` - Extracts text from images (macOS only)
- `removeexif` - Removes EXIF data from images

**Reason:** Require local audio/video playback or processing capabilities not available in container context.

### Local System Control
- `wifi` - Controls system WiFi
- `sleepybear` - Puts system to sleep
- `theme` - Switches dark/light mode
- `notify` - Sends OS notification
- `ds-destroy` - Deletes .DS_Store files (macOS-specific)

**Reason:** Control local system features not applicable to container environments.

### Network/Download Tools
- `getsong` - Downloads from YouTube/SoundCloud
- `getpod` - Downloads video for podcasts
- `getsubs` - Downloads subtitles

**Reason:** Require `yt-dlp` to download media. Not applicable to container inspection.

### REPLs
- `iclj`, `ijs`, `iphp`, `ipy`, `isql` - Language REPLs

**Reason:** While technically possible via exec, interactive REPLs don't fit Cascade's command model well.

### Already Covered or Low Value
- `running` - Process lookup (already have `ps`)
- `catbin` - Shows command source (local PATH)
- `snippets` - Retrieves stored snippets (would need container-side config)

### Complex/Marginal Value
- `murder` - Graceful process termination (would need signals support)
- `waitfor` - Wait for process exit (limited use in container)
- `bb` - Run command in background (exec model doesn't support well)
- `tryna`/`trynafail` - Retry commands (complex, limited use)
- `each` - Alternative to xargs (complex piping)
- `emoji` - Emoji lookup (needs emoji database)

---

## Summary

**Implemented:** 25 commands
- Text Utilities: 10 (line, straightquote, markdownquote, length, jsonformat, uppered, lowered, nato, url, u+)
- System Utilities: 3
- Reference: 2
- Built-in Commands: 6 (mkcd, tempe, mksh, scratch, serveit, rn)
- Clipboard: 4

**Skipped:** ~25 commands (audio/video, system control, etc.)
