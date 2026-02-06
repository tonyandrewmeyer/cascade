# Cascade: POSIX Compliance & Integration Testing Plan

## Goal

Systematically validate that Cascade commands behave like their standard
(POSIX / coreutils / BusyBox) counterparts, and that core shell features work
correctly end-to-end. Fix deviations as we find them. Each command gets its own
PR containing: improved integration tests, any command fixes, and a review of
existing unit tests.

## Current State

The existing integration tests (in `tests/integration/`) run against a real
Pebble instance and verify:

- Command name and category metadata
- Help flag output
- Basic error cases (missing args, nonexistent files)

They do **not** currently test:

- Flag compatibility with the real commands (e.g. `ls -la`, `grep -rn`)
- Output format expectations (column layout, field ordering)
- Exit code semantics matching POSIX (e.g. `grep` returns 1 for no match, not error)
- Interaction between commands via pipes
- Edge cases the real commands handle

## Approach

### Per-Command PR Workflow

For each command (one PR per command, working through the priority list in
`command-tracking.md`):

1. **Research the standard.** Look up the POSIX spec, coreutils man page, or
   BusyBox docs for the command. Identify which flags and behaviors Cascade
   should support. Note anything we intentionally skip (and why).

2. **Write integration tests.** Add tests to `tests/integration/test_<cmd>command.py`
   that validate standard-conforming behavior:
   - Common flag combinations
   - Output format (where it matters — exact column layout for `ls -l`, etc.)
   - Exit codes matching the standard
   - Edge cases (empty input, binary files, missing permissions, symlinks)
   - Any Cascade enhancements (color, Rich formatting) tested separately so
     they don't break standard-behavior assertions

3. **Fix the command.** Make the tests pass. Where behavior diverges from the
   standard, either fix it or document the deviation with a comment in the test
   explaining why (e.g. "Pebble API doesn't expose permissions").

4. **Review unit tests.** Check the corresponding unit tests in
   `tests/unit/test_commands/` and `tests/unit/test_utils/`. Add coverage for
   anything the integration tests exposed. Remove tests that duplicate
   integration coverage without adding value.

5. **Update the tracking doc.** Mark the command as done in
   `command-tracking.md`.

### What "Compliance" Means

Cascade operates over Pebble's API, not a real filesystem, so full POSIX
compliance is impossible. The target is:

- **Flags:** Support the most-used flags. Document unsupported ones in the
  command's help text.
- **Output format:** Match the standard format by default. Rich/color
  enhancements are fine but should not break parseable output when piped
  (i.e. no ANSI codes in piped output).
- **Exit codes:** Match POSIX exit code semantics (0 success, 1 operational
  failure, 2 usage error — or command-specific codes like `grep`'s).
- **Argument parsing:** Flags should work the way users expect. `-abc` should
  be equivalent to `-a -b -c` where applicable. `--long-flag=value` and
  `--long-flag value` should both work.
- **Known limitations:** Where Pebble can't provide something (e.g. file
  ownership, block devices), the command should degrade gracefully and
  document the gap.

### Testing Conventions

- Integration tests go in `tests/integration/test_<commandname>command.py`
  (existing files, extend them).
- Tests that need filesystem state should create temp files via Pebble's
  `push` API in fixtures and clean up after.
- Use `command.shell.console.capture()` to capture output.
- Use `@pytest.mark.integration` (auto-applied by conftest for files in the
  integration directory).
- For testing piped behavior, use the `PipelineExecutor` directly or test
  through `PebbleShell`'s command dispatch.

## Shell Feature Testing

After the initial batch of command work, or interleaved as desired, we need
integration tests for the core shell machinery. These go in a new file:
`tests/integration/test_shell_features.py`.

### Features to Test

| Feature | What to validate |
|---------|-----------------|
| **Pipes (`\|`)** | Output of one command feeds into the next. Multi-stage pipes. Exit code is from the last command. |
| **Output redirection (`>`, `>>`)** | Creates/overwrites file. Appends to file. Works with any command. |
| **Command chaining (`;`)** | Both commands run regardless of exit codes. |
| **AND chaining (`&&`)** | Second command only runs if first succeeds. |
| **OR chaining (`\|\|`)** | Second command only runs if first fails. |
| **Variable expansion (`$VAR`)** | Assignment, expansion in args, `${VAR}` form, special vars (`$?`, `$HOME`). |
| **Glob expansion (`*`, `?`)** | Expands against remote filesystem. No expansion when quoted. |
| **Tilde expansion (`~`)** | Expands to detected home directory. Works in paths like `~/foo`. |
| **For-loops** | `for x in a b c; do echo $x; done` — correct iteration, variable scoping. |
| **Aliases** | Definition, expansion, expansion with args, nested aliases (or lack thereof). |
| **History expansion** | `!!`, `!n`, `!-n`, `!$` — correct substitution. |
| **Quoting** | Single quotes preserve literal text. Double quotes allow variable expansion. Mixed quoting. Escaped characters. |
| **Tab completion** | Command name completion. Path completion on the remote filesystem. |
| **Exit codes (`$?`)** | Correctly reflects last command. Propagated through chains. |

### Testing Approach for Shell Features

Shell feature tests need to exercise the full pipeline: input string →
parser → executor → command → output. The pattern will be:

```python
def test_pipe_two_commands(shell, client):
    """echo 'hello world' | wc -w should output 2."""
    output = run_shell_command(shell, client, "echo 'hello world' | wc -w")
    assert output.strip() == "2"
```

We'll need a helper like `run_shell_command()` that feeds a command string
through the shell's full dispatch path and captures output. This can be built
on top of `PebbleShell.onecmd()` or the parser + executor directly.

## Reference Standards

For each command, the primary reference is (in order of precedence):

1. **POSIX.1-2024** (IEEE Std 1003.1) — for commands in the POSIX spec
2. **GNU coreutils** documentation — for common extensions
3. **BusyBox** documentation — since Cascade targets minimal containers,
   BusyBox behavior is often the more relevant baseline
4. **Pebble CLI** documentation — for Pebble-specific commands

Commands that have no POSIX equivalent (dashboard, theme, pebblesay, info,
etc.) are tested against their own documented behavior.
