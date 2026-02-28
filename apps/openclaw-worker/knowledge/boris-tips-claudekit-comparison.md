# Boris Tips (Claude Code Creator) × ClaudeKit Comparison

> Source: Minh Long post (2026-02-03) — Boris tips from Anthropic team
> Classification: STRATEGIC INTEL — 知彼知己 Know Yourself Know Enemy
> Date: 2026-02-18

## Boris's 10 Tips (From Anthropic Team's Daily Usage)

### 1. Parallel Worktrees (3-5 sessions)
- Productivity unlock: 3-5 git worktrees simultaneously
- Aliases: za, zb, zc for quick switching
- Some keep "analysis" worktree for logs/BigQuery
- **CK Coverage:** ✅ /worktree skill + orchestration protocol
- **Tôm Hùm Gap:** ⚠️ Using tmux but not git worktrees → CCPM will fix

### 2. Plan Mode First
- Invest heavily in plan → Claude 1-shot implementation
- 1 Claude writes plan, 1 Claude reviews as staff engineer
- **CK Coverage:** ✅ 5 plan variations + /plan:validate
- **Tôm Hùm:** ✅ Covered via /plan:hard through proxy

### 3. CLAUDE.md Investment
- "Update your CLAUDE.md so you don't make that mistake again"
- Claude writes its own rules → iterate until mistake rate drops
- Engineer maintains notes directory per task/project
- **CK Coverage:** ✅ Over-covered — structured hierarchy + auto triggers
- **Tôm Hùm:** ✅ Covered

### 4. Reusable Skills
- Anything done >1x/day → turn into skill/command
- /techdebt command end of session
- Sync 7 days Slack/GDrive/Asana/GitHub into context dump
- **CK Coverage:** ✅ 73+ pre-built + /skill-creator
- **Tôm Hùm:** ✅ 80+ skills

### 5. Claude Self-Fix Bugs
- Slack MCP → paste bug thread → "fix"
- "Go fix the failing CI tests" — zero context switching
- Point Claude at docker logs for distributed systems
- **CK Coverage:** ✅ /fix + debugger agent (routes by bug type)
- **Tôm Hùm:** ✅ Proxy-driven

### 6. Advanced Prompting
- "Grill me on these changes"
- "Prove to me this works" — diff main vs feature
- "Knowing everything you know now, scrap this and implement elegant solution"
- **CK Coverage:** ✅ /brainstorm, /code-review, /plan:validate, code-simplifier
- **Tôm Hùm:** ✅ Via ClaudeKit

### 7. Terminal Setup
- Ghostty terminal (sync rendering, 24-bit color)
- /statusline: context usage %, git branch
- Color-code tabs + name tabs
- Voice dictation: fn×2 on macOS
- **CK Coverage:** ✅ Statusline 4 modes (full/compact/minimal/none)
- **Tôm Hùm Gap:** ⚠️ tmux basic — need to enable CK statusline

### 8. Subagents
- "use subagents" → spawn parallel agents
- Keep main context clean
- Route permissions via Opus 4.5 auto-approve
- **CK Coverage:** ✅ Pre-configured agent types + orchestration protocol
- **Tôm Hùm:** ✅ CTO + task-watcher pattern

### 9. Data & Analytics
- BigQuery skill in repo — Boris hasn't touched SQL in 6 months
- Claude writes SQL → runs → analyzes → answers
- **CK Coverage:** ❌ NO SKILL YET
- **Tôm Hùm Gap:** 🔴 Need analytics/BigQuery/Supabase skill

### 10. Learn with Claude
- "Explanatory" output in /config
- HTML slides for code explanation
- ASCII diagrams for protocols
- Spaced-repetition skill
- **CK Coverage:** ⚠️ Partial (mermaid, researcher, coding-level)
- **Tôm Hùm Gap:** 🟡 Missing learning mode, HTML slides, spaced-repetition

## GAP ANALYSIS

| Gap | Priority | Solution |
|:----|:---------|:---------|
| Git worktrees | P1 | CCPM task (already created!) |
| Data/Analytics skill | P2 | Create Supabase/BigQuery analytics skill |
| CK statusline enable | P2 | Enable in settings |
| Learning mode | P3 | Nice to have |

## Shout-outs
- **Boris** (Claude Code creator) — tips from actual daily usage
- **Minh Long** — excellent analysis and comparison
- **Duy Nguyen** (CK Creator) + **Kai** (CK Maintainer) — 7/10 already covered!
