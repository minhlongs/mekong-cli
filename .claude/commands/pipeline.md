---
description: "Run multi-agent pipeline (FilePicker -> Editor -> Reviewer). 3-5 MCU."
argument-hint: [goal description]
allowed-tools: Read, Write, Bash, Task
---

# /core:pipeline — Multi-Agent Pipeline

**Super command** — runs FilePicker -> Editor -> Reviewer sequentially.

## Pipeline

```
SEQUENTIAL:
├── file-picker  → scan codebase, surface relevant files
├── editor       → apply edits based on file-picker output
└── reviewer     → validate changes, check regressions
```

## Usage

```
mekong pipeline "add error handling to auth.py"
mekong pipeline "refactor the API layer" --stages file-picker,editor,reviewer
mekong pipeline "fix the login bug" --json
mekong pipeline "update config" --verbose
```

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--stages` | file-picker,editor,reviewer | Comma-separated agent names |
| `--json` / `-j` | false | Machine-readable JSON output |
| `--verbose` / `-v` | false | Show per-stage output |

## Output

- Rich table with stage status and duration
- Final pass/fail verdict
- Per-stage output in verbose mode

## MCU Cost

3-5 credits depending on stage complexity.
