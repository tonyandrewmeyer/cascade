# Command Compliance Tracking

Status key: ` ` = not started, `~` = in progress, `x` = done

Commands are grouped into priority tiers based on how frequently they're
needed when debugging containers. Work through them in order.

See `testing-plan.md` for the per-command workflow.

---

## Tier 1 — Essential (use every session)

These are the first commands anyone reaches for in a debugging shell.

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `ls` | Yes | `-l`, `-a`, `-R`, `-t`, `-S`, `-h`, `-1`; color is a Cascade enhancement |
| [ ] | `cat` | Yes | `-n`, `-b`, `-E`, `-T`; multiple files |
| [ ] | `cd` | Yes | Relative, absolute, `~`, `-` (previous dir), no-arg goes to `~` |
| [ ] | `pwd` | Yes | Should just work |
| [ ] | `echo` | Yes | `-n`, `-e` (escape sequences); BusyBox behavior for `-e` is default-on |
| [ ] | `head` | Yes | `-n`, `-c`; default 10 lines; multiple files with headers |
| [ ] | `tail` | Yes | `-n`, `-c`; default 10 lines; `-n +N` for offset |
| [ ] | `grep` | Yes | `-i`, `-v`, `-n`, `-c`, `-l`, `-r`, `-E`, `-F`, `-w`; exit code 1 = no match |
| [ ] | `find` | Yes | `-name`, `-type`, `-size`, `-mtime`, `-exec`, `-print`; subset is fine |
| [ ] | `stat` | Yes | File metadata; format may differ from GNU stat |
| [ ] | `wc` | Yes | `-l`, `-w`, `-c`, `-m`; multiple files with totals |
| [ ] | `env` | Yes | No args = print all; `env VAR=val cmd` form |
| [ ] | `printenv` | Yes | Print one or all env vars |
| [ ] | `ps` | Yes | Process listing; format will differ (reads /proc) |
| [ ] | `which` | Yes | Locate commands; exit 1 if not found |

## Tier 2 — Core manipulation & text processing

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `cp` | Yes | `-r`, `-f`, `-p`; recursive copy |
| [ ] | `mv` | Yes | `-f`, `-i` |
| [ ] | `rm` | Yes | `-r`, `-f`; no `-rf /` safeguard needed (Pebble limits) |
| [ ] | `mkdir` | Yes | `-p` for parents |
| [ ] | `touch` | Yes | Create file or update timestamp |
| [ ] | `rmdir` | Yes | Only empty dirs |
| [ ] | `sort` | Yes | `-n`, `-r`, `-k`, `-t`, `-u`; stable sort |
| [ ] | `uniq` | Yes | `-c`, `-d`, `-u`; requires sorted input |
| [ ] | `cut` | Yes | `-d`, `-f`, `-c`; field and character modes |
| [ ] | `diff` | Yes | Unified diff format; exit code 0=same 1=different |
| [ ] | `sed` | Yes | `s///`, addresses, `-i`, `-n`, `-e`; subset of full sed is fine |
| [ ] | `tr` | Yes | Character translation and deletion; `-d`, `-s`, `-c` |
| [ ] | `tee` | Yes | `-a` for append; pass stdin to stdout and file(s) |
| [ ] | `less` | No | Pager; may be limited given no terminal control over Pebble |
| [ ] | `more` | Yes | Pager; same limitation note |

## Tier 3 — System info & monitoring

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `df` | Yes | `-h`, `-i`; filesystem usage |
| [ ] | `du` | Yes | `-h`, `-s`, `-d`/`--max-depth` |
| [ ] | `free` | No | Linux-specific; `-h`, `-m`, `-g` |
| [ ] | `uname` | Yes | `-a`, `-s`, `-r`, `-m`, `-n` |
| [ ] | `hostname` | Yes | Display hostname |
| [ ] | `id` | Yes | `-u`, `-g`, `-n`; uid/gid/groups |
| [ ] | `whoami` | Yes | Print effective user |
| [ ] | `date` | Yes | Format strings (`+%Y-%m-%d`); display only (no set) |
| [ ] | `uptime` | No | Linux-style output |
| [ ] | `top` | No | Process monitor; display-only snapshot is fine |
| [ ] | `mount` | Yes | Display mounts (read-only) |
| [ ] | `dmesg` | No | Kernel log; read from /proc or Pebble |
| [ ] | `w` | No | Who is logged in; limited in containers |
| [ ] | `who` | No | Same |
| [ ] | `last` | No | Login history; limited |
| [ ] | `lsof` | No | Open files; limited |
| [ ] | `pgrep` | No | `-f`, `-l`; process name matching |
| [ ] | `pstree` | No | Process tree display |
| [ ] | `vmstat` | No | Virtual memory stats |
| [ ] | `iostat` | No | IO statistics |
| [ ] | `cpuinfo` | No | CPU information |
| [ ] | `meminfo` | No | Memory information |
| [ ] | `loadavg` | No | Load averages |

## Tier 4 — Network diagnostics

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `ip` | No | `ip addr`, `ip route`, `ip link`, `ip rule`; iproute2-style |
| [ ] | `ifconfig` | No | Legacy but people still use it; interface listing |
| [ ] | `netstat` | No | `-t`, `-u`, `-l`, `-n`, `-p`; connection listing |
| [ ] | `ss` | No | Modern netstat replacement |
| [ ] | `route` | No | Routing table display |
| [ ] | `arp` | No | ARP table display |
| [ ] | `dnsdomainname` | No | DNS domain |

## Tier 5 — Utilities & shell features

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `alias` | Yes | Define and list aliases |
| [ ] | `history` | No | Bash-style history listing |
| [ ] | `test` / `[` / `[[` | Yes/No | `-f`, `-d`, `-e`, `-z`, `-n`, string/numeric comparisons |
| [ ] | `printf` | Yes | Format strings; more portable than `echo -e` |
| [ ] | `sleep` | Yes | Integer and fractional seconds |
| [ ] | `time` | Yes | Command timing |
| [ ] | `timeout` | No | GNU coreutils; run command with time limit |
| [ ] | `xargs` | Yes | `-I{}`, `-n`, `-d`; build commands from stdin |
| [ ] | `tar` | Yes | `-c`, `-x`, `-t`, `-z`, `-j`, `-f`; create/extract/list |
| [ ] | `gzip` / `gunzip` | Yes | Compress/decompress |
| [ ] | `bzip2` / `bunzip2` | No | Compress/decompress |
| [ ] | `true` / `false` | Yes | Exit 0 / exit 1 |
| [ ] | `cal` | No | Calendar display |
| [ ] | `watch` | No | Repeat command periodically |

## Tier 6 — Specialized tools

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `jq` | No | JSON processing |
| [ ] | `yq` | No | YAML processing |
| [ ] | `md5sum` | No | Hash computation |
| [ ] | `sha256sum` | No | Hash computation |
| [ ] | `sha1sum` | No | Hash computation |
| [ ] | `sha512sum` | No | Hash computation |
| [ ] | `cksum` | Yes | CRC checksum |
| [ ] | `basename` | Yes | Strip directory from path |
| [ ] | `dirname` | Yes | Strip filename from path |
| [ ] | `realpath` | No | Resolve symlinks/relative path |
| [ ] | `readlink` | No | Read symlink target |
| [ ] | `cmp` | Yes | Byte-by-byte file comparison |
| [ ] | `comm` | Yes | Compare sorted files line by line |
| [ ] | `dd` | Yes | Block-level copy; limited flags needed |
| [ ] | `od` | Yes | Octal/hex dump |
| [ ] | `hexdump` / `hd` | No | Hex dump display |
| [ ] | `split` | Yes | Split file into pieces |
| [ ] | `seq` | No | Generate number sequences |
| [ ] | `fold` | Yes | Wrap lines to width |
| [ ] | `expand` / `unexpand` | Yes | Tab/space conversion |
| [ ] | `expr` | Yes | Expression evaluation |
| [ ] | `dc` | Yes | Desk calculator (RPN) |
| [ ] | `strings` | Yes | Extract printable strings from binary |
| [ ] | `tac` | No | Reverse cat (lines in reverse) |
| [ ] | `dos2unix` / `unix2dos` | No | Line ending conversion |
| [ ] | `mktemp` | No | Create temporary file/directory |
| [ ] | `getopt` | No | Parse command options |
| [ ] | `ipcalc` | No | IP address calculator |

## Tier 7 — Niche & rarely used

| Status | Command | POSIX | Notes |
|--------|---------|-------|-------|
| [ ] | `ar` | Yes | Archive utility |
| [ ] | `cpio` | Yes | Archive copy |
| [ ] | `compress` / `uncompress` | Yes | Legacy compression |
| [ ] | `lzma` / `unlzma` / `lzmacat` | No | LZMA compression |
| [ ] | `unzip` | No | ZIP extraction |
| [ ] | `patch` | Yes | Apply diffs |
| [ ] | `script` / `scriptreplay` | No | Session recording |
| [ ] | `ulimit` | Yes | Resource limits display |
| [ ] | `sysctl` | No | Kernel parameters |
| [ ] | `lsmod` | No | Kernel modules |
| [ ] | `tty` / `ttysize` | Yes/No | Terminal info |
| [ ] | `logname` | Yes | Login name |
| [ ] | `runlevel` | No | System runlevel |
| [ ] | `fuser` | No | Processes using files |
| [ ] | `pidof` | No | Find PID by name |
| [ ] | `logger` | Yes | Write to syslog |
| [ ] | `hostid` | Yes | Host identifier |
| [ ] | `usleep` | No | Microsecond sleep |
| [ ] | `yes` | No | Repeat string |
| [ ] | `adduser` / `deluser` | No | User management |
| [ ] | `addgroup` / `delgroup` | No | Group management |
| [ ] | `mkpasswd` / `cryptpw` | No | Password utilities |
| [ ] | `dumpkmap` / `dumpleases` | No | BusyBox-specific |
| [ ] | `readprofile` | No | Kernel profiling |
| [ ] | `fdinfo` | No | File descriptor info |
| [ ] | `blkid` / `findfs` / `volname` | No | Block device info |
| [ ] | `lsattr` | No | File attributes |
| [ ] | `mountpoint` | No | Check if path is a mountpoint |
| [ ] | `sum` | Yes | File checksum (legacy) |
| [ ] | `ipcs` | Yes | IPC status |

## Pebble-Specific Commands

These don't follow POSIX — test against Pebble's own expected behavior.

| Status | Command | Notes |
|--------|---------|-------|
| [ ] | `services` | List services; match `pebble services` output format |
| [ ] | `start` / `stop` / `restart` | Service lifecycle |
| [ ] | `logs` | Service logs; `-f` follow, `-n` lines |
| [ ] | `checks` / `start-checks` / `stop-checks` | Health checks |
| [ ] | `plan` | Show current plan |
| [ ] | `replan` | Reload plan |
| [ ] | `add` | Add layer |
| [ ] | `changes` / `tasks` | Change tracking |
| [ ] | `notices` / `notice` / `notify` | Notice system |
| [ ] | `health` / `check` | Health status |
| [ ] | `pull` / `push` | File transfer |
| [ ] | `signal` | Send signal to service |
| [ ] | `pebble` | Pebble system info |

## Cascade-Only Commands

No external standard — test against documented/intended behavior.

| Status | Command | Notes |
|--------|---------|-------|
| [ ] | `dashboard` | System overview display |
| [ ] | `info` | System information panel |
| [ ] | `theme` | Theme management |
| [ ] | `edit` | In-shell file editor |
| [ ] | `pebblesay` | Fun output (cowsay-style) |
| [ ] | `beep` | Terminal bell |
| [ ] | `clear` / `reset` | Terminal clear |
| [ ] | `markdown` / `md` | Render markdown |
| [ ] | `local` | Shell-local variable |
| [ ] | `exec` | Execute command on Pebble |
| [ ] | `shell` | Drop to Pebble exec shell |
| [ ] | `run` / `run-parts` | Run commands/scripts |
| [ ] | `envdir` | Run with env from directory |
| [ ] | `net` | Network overview |
| [ ] | `syslog` | Syslog viewer |
| [ ] | `pstrace` | Process trace |

## Shell Features

Tracked separately — these cut across all commands.

| Status | Feature | Notes |
|--------|---------|-------|
| [ ] | Pipes (`\|`) | Multi-stage; exit code from last command |
| [ ] | Output redirection (`>`, `>>`) | Create, overwrite, append |
| [ ] | Command chaining (`;`) | Run both regardless |
| [ ] | AND chaining (`&&`) | Short-circuit on failure |
| [ ] | OR chaining (`\|\|`) | Short-circuit on success |
| [ ] | Variable assignment & expansion | `$VAR`, `${VAR}`, `$?` |
| [ ] | Glob expansion | `*`, `?`, `[...]`; no expansion in quotes |
| [ ] | Tilde expansion | `~`, `~/path` |
| [ ] | For-loops | `for x in ...; do ...; done` |
| [ ] | Aliases | Define, expand, list |
| [ ] | History expansion | `!!`, `!n`, `!$` |
| [ ] | Quoting | Single, double, escaping |
| [ ] | Tab completion | Commands and remote paths |
| [ ] | Exit codes | Correct propagation through all features |
