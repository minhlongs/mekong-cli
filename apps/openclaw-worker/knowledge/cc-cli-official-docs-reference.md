# Claude Code Official Docs Reference

> Source: code.claude.com/docs (Anthropic Official)
> Classification: CANON — Source of truth for CC CLI
> Date: 2026-02-18

## Key URLs

- Overview: https://code.claude.com/docs
- Best Practices: https://code.claude.com/docs/en/best-practices
- Subagents: https://code.claude.com/docs/en/sub-agents
- Skills: https://code.claude.com/docs/en/skills
- Hooks: https://code.claude.com/docs/en/hooks
- MCP: https://code.claude.com/docs/en/mcp
- Agent Teams: https://code.claude.com/docs/en/agent-teams
- Common Workflows: https://code.claude.com/docs/en/common-workflows
- Desktop: https://code.claude.com/docs/en/desktop
- Web: https://code.claude.com/docs/en/claude-code-on-the-web
- Slack: https://code.claude.com/docs/en/slack
- Chrome: https://code.claude.com/docs/en/chrome
- Agent SDK: https://platform.claude.com/docs/en/agent-sdk/overview

## Quick Wins For Tôm Hùm

1. **Background subagents** — Ctrl+B to background a running task
2. **Fan-out** — for file; do claude -p "task $file"; done
3. **Named sessions** — /rename "feature-name" + claude --resume
4. **Custom compaction** — /compact Focus on X + CLAUDE.md compaction rules
5. **Subagent chaining** — Reviewer → Optimizer pattern

## Anti-Patterns To Avoid

1. Kitchen sink session → /clear between tasks
2. Correcting 3+ times → /clear + rewrite prompt
3. Over-specified CLAUDE.md → Ruthlessly prune
4. Trust-then-verify gap → Always provide verification
5. Infinite exploration → Scope narrowly or use subagents
