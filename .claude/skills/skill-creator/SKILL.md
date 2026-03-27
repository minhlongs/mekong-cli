---
name: skill-creator
description: Create new Mekong CLI skills from observed Claude failure patterns, repetitive workflows, or codebase-specific knowledge. Trigger when user says "make a skill for", "create skill", "this should be a skill", or when Claude notices it's doing the same multi-step task for the third time.
---

# Skill Creator

## When to Create a Skill
- You've done the same multi-step task 3+ times
- Claude keeps hitting the same gotcha in this codebase
- A workflow requires codebase-specific knowledge Claude doesn't have by default
- A verification step needs specific scripts or assertions

## How to Create a Skill

### Step 1: Choose the category
Read `.claude/skills/README.md` for the 9 categories. Pick ONE.

### Step 2: Create the folder structure
```bash
SKILL_NAME="<kebab-case-name>"
mkdir -p .claude/skills/$SKILL_NAME/{scripts,references,assets}
```

### Step 3: Write SKILL.md
Use this template (in `assets/skill-template.md`):
- **Description**: Write for the MODEL. When should Claude trigger this? Be specific about trigger phrases.
- **Don't state the obvious**: Only include what pushes Claude out of default behavior.
- **Gotchas**: Start with at least 2 known failure points. Add more over time.

### Step 4: Add scripts if needed
Scripts in `scripts/` should be:
- Executable (`chmod +x`)
- Self-contained (no external deps not in the repo)
- Composable (take stdin, output stdout)
- Documented with `--help`

### Step 5: Test the skill
Ask Claude to use the skill in a fresh session. Did it trigger correctly? Did it avoid the gotchas?

## Gotchas
- Don't make skills that just restate what Claude already knows about coding
- Description must be specific — vague descriptions undertrigger
- One skill per purpose — don't straddle categories
- Keep SKILL.md under 200 lines — use progressive disclosure for details
