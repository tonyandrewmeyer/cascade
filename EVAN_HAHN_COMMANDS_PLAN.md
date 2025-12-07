# Evan Hahn Scripts - Implementation Plan for Cascade

This document analyzes scripts from [Evan Hahn's blog post](https://evanhahn.com/scripts-i-wrote-that-i-use-all-the-time/) and evaluates which ones make sense to implement in Cascade.

## Context: What is Cascade?

Cascade is a Pebble shell for interacting with containers/workloads. It has:
- Filesystem read/write access to containers via Pebble client
- Exec capability for running commands in containers
- Rich terminal output via the Rich library
- **No local system access** (clipboard, audio, video, GUI, etc.)

This context is crucial for evaluating which scripts are feasible.

---

## Commands to Implement

These commands can be implemented using Python and filesystem/exec capabilities:

### Text Processing

| Command | Description | Implementation Notes |
|---------|-------------|---------------------|
| `line` | Extract specific line number from stdin | Pure text processing, read from stdin |
| `straightquote` | Convert smart quotes to straight quotes | String replacement |
| `markdownquote` | Add `>` prefix to each line | Text transformation |
| `length` | Return character count of argument | Simple `len()` |
| `jsonformat` | Pretty-print JSON from stdin | Use Python's `json` module |
| `uppered` | Convert string to uppercase | `str.upper()` |
| `lowered` | Convert string to lowercase | `str.lower()` |
| `nato` | Convert letters to NATO phonetic alphabet | Static lookup table |

### Date/Time

| Command | Description | Implementation Notes |
|---------|-------------|---------------------|
| `hoy` | Print current date in ISO format (YYYY-MM-DD) | Use existing date infrastructure |

### Reference/Lookup

| Command | Description | Implementation Notes |
|---------|-------------|---------------------|
| `httpstatus` | Display HTTP status code descriptions | Static data lookup |
| `alphabet` | Print English alphabet | Trivial static output |

### System/Utilities

| Command | Description | Implementation Notes |
|---------|-------------|---------------------|
| `uuid` | Generate v4 UUID | Python's `uuid` module |
| `prettypath` | Display PATH with newlines | Read from container environment |

---

## Commands to Skip

### Clipboard Commands (No local system access)
- `copy` - Pipes output to system clipboard
- `pasta` - Retrieves clipboard contents
- `pastas` - Monitors clipboard changes
- `cpwd` - Copies current directory to clipboard

**Reason:** Require access to the local system's clipboard, which is not available when operating on remote containers.

### Local Editor/Terminal Commands
- `mkcd` - Creates directory and `cd` into it
- `tempe` - `cd` to temporary directory
- `mksh` - Creates shell script and opens in Vim
- `scratch` - Opens temporary Vim buffer

**Reason:** These change local directory or open local editors. The container doesn't have an interactive editor session.

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
- `serveit` - Starts local file server
- `getsong` - Downloads from YouTube/SoundCloud
- `getpod` - Downloads video for podcasts
- `getsubs` - Downloads subtitles

**Reason:** Require `yt-dlp` or start servers on local machine. Not applicable to container inspection.

### REPLs
- `iclj`, `ijs`, `iphp`, `ipy`, `isql` - Language REPLs

**Reason:** While technically possible via exec, interactive REPLs don't fit Cascade's command model well.

### Already Covered or Low Value
- `running` - Process lookup (already have `ps`)
- `catbin` - Shows command source (local PATH)
- `url` - URL parser (less useful in container context)
- `trash` - Moves to trash (container doesn't have trash)
- `snippets` - Retrieves stored snippets (would need container-side config)

### Complex/Marginal Value
- `murder` - Graceful process termination (would need signals support)
- `waitfor` - Wait for process exit (limited use in container)
- `bb` - Run command in background (exec model doesn't support well)
- `tryna`/`trynafail` - Retry commands (complex, limited use)
- `each` - Alternative to xargs (complex piping)
- `u+` - Unicode lookup (needs Unicode database)
- `emoji` - Emoji lookup (needs emoji database)
- `rn` - Time with calendar (already have `date` and `cal`)

---

## Implementation Order

Priority based on usefulness and simplicity:

1. **`uuid`** - Very simple, immediately useful
2. **`hoy`** - Simple date formatting
3. **`httpstatus`** - Useful reference tool
4. **`alphabet`** - Trivial to implement
5. **`length`** - Simple utility
6. **`uppered`/`lowered`** - Simple text transforms
7. **`jsonformat`** - Useful for inspecting JSON files
8. **`line`** - Useful for text processing
9. **`straightquote`** - Text cleanup utility
10. **`markdownquote`** - Text formatting utility
11. **`nato`** - Fun reference tool
12. **`prettypath`** - Debugging utility

---

## Category Assignment

These commands will be placed in the following categories:

- **Text Utilities**: `line`, `straightquote`, `markdownquote`, `length`, `jsonformat`, `uppered`, `lowered`, `nato`
- **System Utilities**: `uuid`, `hoy`, `prettypath`
- **Reference**: `httpstatus`, `alphabet`
