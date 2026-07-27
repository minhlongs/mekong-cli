# .claude/_pipeline/ — Đường ống / Pipeline

## VN
Thư mục **đường ống thực thi** — hooks, archived commands, build scripts.

## EN
**Execution pipeline** directory — hooks, archived commands, build scripts.

### Contents / Nội dung
| Dir / Thư mục | Mục đích / Purpose |
|---|---|
| `hooks/` | 25 hook executables (.cjs, .sh) — lifecycle events |
| `command-archive/` | Archived command definitions (legacy/migration) |
| `scripts/` | Build/utility scripts (scan, validate, worktree, bridge) |
| `lib/` | Shared hook libraries |

### Hooks lifecycle / Vòng đời hooks
- `SessionStart` → `session-init.cjs`, `zunef-model-purge.cjs`
- `UserPromptSubmit` → `dev-rules-reminder.cjs`, `simplify-gate.cjs`
- `PreToolUse` → `pre-tool-use-guard.cjs`
- `PostToolUse` → `plan-format-kanban.cjs`, `session-state.cjs`
- `SubagentStart/Stop` → `subagent-init.cjs`, `cook-after-plan-reminder.cjs`

### Quy tắc / Rules
**DOANH TRẠI (Garrison):** Read-write. Tự do edit.
