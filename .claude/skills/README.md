# Mekong CLI Skills

Skills are folders that extend OpenClaw's capabilities. Each contains:
- `SKILL.md` — Entry point. Model reads this to decide when/how to use the skill.
- `scripts/` — Executable scripts Claude can run directly.
- `references/` — API docs, code snippets, gotchas for Claude to read on demand.
- `assets/` — Templates, data files, config schemas.

## Skill Categories (Thariq Framework)
1. Library & API Reference
2. Product Verification
3. Data Fetching & Analysis
4. Business Process & Automation
5. Code Scaffolding & Templates
6. Code Quality & Review
7. CI/CD & Deployment
8. Runbooks
9. Infrastructure Operations

## Adding a Skill
```bash
mekong cook "create a new skill for <purpose>"
# Or manually:
mkdir -p .claude/skills/<skill-name>/{scripts,references,assets}
# Edit .claude/skills/<skill-name>/SKILL.md
```
