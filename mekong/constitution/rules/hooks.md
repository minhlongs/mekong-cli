# CK Init Hooks Standard

Canonical hook structure for ALL projects.

## Hook Events

| Event | Required Hooks |
|-------|---------------|
| SessionStart | `session-init.cjs`, `usage-quota-cache-refresh.cjs` |
| UserPromptSubmit | `user-prompt-routing.cjs`, `simplify-gate.cjs`, `dev-rules-reminder.cjs`, `usage-quota-cache-refresh.cjs` |
| SubagentStart | `subagent-init.cjs` |
| PreToolUse | `descriptive-name.cjs` (Write), `scout-block.cjs` + `privacy-block.cjs` (Bash/Read/Edit/Write) |
| PostToolUse | `plan-format-kanban.cjs` (Edit/Write), `session-state.cjs` + `usage-quota-cache-refresh.cjs` (Task) |
| SubagentStop | `cook-after-plan-reminder.cjs` (Plan), `session-state.cjs` |
| Stop | `session-state.cjs` |

## Status Line

```json
"statusLine": {
  "type": "command",
  "command": "node \"$HOME/.claude/statusline.cjs\"",
  "padding": 0
}
```

## Env Vars (all profiles)

- `CLAUDE_CODE_EFFORT_LEVEL: "ultracode"`
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "true"`
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: "1"`
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW: "900000"`
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: "90"`
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS: "128000"`
- `CLAUDE_ENABLE_STREAM_WATCHDOG: "1"`
- `CLAUDE_STREAM_IDLE_TIMEOUT_MS: "360000"`

## ZuneF-Specific Overrides

- `ANTHROPIC_BASE_URL: "https://claude.zunef.com/v1/ai"`
- `CLAUDE_CODE_AUTO_COMPACT_WINDOW: "230000"` (262k context)
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE: "75"` (compact sớm)
- `ENABLE_TOOL_SEARCH: "false"`
- Add `zunef-jwt-reminder.cjs` to UserPromptSubmit
