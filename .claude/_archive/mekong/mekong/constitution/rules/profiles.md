# Claude Code — 3 Profile Standard

## Architecture

```
┌──────────────────────────────────────────────┐
│            CK Init (hooks + statusLine)       │
├──────────┬──────────────┬────────────────────┤
│ cc       │ deepseek     │ claude             │
│ ZuneF    │ DeepSeek V4  │ Anthropic Official │
│ Opus 4.8 │ Flash 85%    │ Opus 4.8 thật      │
│ JWT 15ph │ Pro 15%      │ Static key         │
└──────────┴──────────────┴────────────────────┘
```

## Profile Locations

| Command | Settings File |
|---------|--------------|
| `cc` | `~/.claude/settings-zunef.json` |
| `deepseek` | `~/.claude/settings-deepseek.json` |
| `claude` | `~/.claude/settings-claude.json` |
| (default) | `~/.claude/settings.json` (DeepSeek) |

## Shell Functions (`.zshrc`)

```bash
function cc() {
  unset ANTHROPIC_AUTH_TOKEN
  # Pre-flight: check ZuneF auth -> fallback to DeepSeek if down
  ...
  command claude --dangerously-skip-permissions --settings "$HOME/.claude/settings-zunef.json" "$@"
}

deepseek() {
  exec command claude --settings "$HOME/.claude/settings-deepseek.json" "$@"
}

claude() {
  unalias claude 2>/dev/null || true
  command claude --dangerously-skip-permissions --settings "$HOME/.claude/settings-claude.json" "$@"
}
```

## ZuneF Auth (JWT Workaround)

- JWT expires in 15 minutes (server-side)
- Solution: MANDATORY Workflow — ALL tasks spawn subagents
- Each subagent = fresh process = fresh JWT
- Hook `zunef-jwt-reminder.cjs` injects this instruction on every prompt

## Supported Models

| Profile | Default | Opus | Sonnet | Haiku |
|---------|---------|------|--------|-------|
| cc (ZuneF) | opus-4-8 | opus-4-8 | opus-4-7 | opus-4-6 |
| deepseek | flash[1m] | pro[1m] | flash[1m] | flash[1m] |
| claude | sonnet-4-6 | opus-4-8 | sonnet-4-6 | haiku-4-5 |
