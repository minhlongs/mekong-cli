---
description: 🚀 VIBE 6-step development workflow with Binh Phap integration
argument-hint: [plan]
---

## Mission

Run the VIBE 6-step development workflow on an implementation plan.

**MUST READ** `CLAUDE.md` then start working on the plan following the VIBE Development Cycle.

<plan>$ARGUMENTS</plan>

---

## 6-Step Workflow

### Step 0: Plan Detection

```
IF $ARGUMENTS is empty:
  → Find latest plan.md in ./plans
IF $ARGUMENTS provided:
  → Use that plan
```

**Output:** `✅ Step 0: [Plan Name] - [Phase Name]`

---

### Step 1: Analysis & Task Extraction

- Read plan file completely
- Map dependencies between tasks
- List ambiguities or blockers
- Activate required skills

**Output:** `✅ Step 1: Found [N] tasks - Ambiguities: [list]`

---

### Step 2: Implementation

Follow YAGNI/KISS/DRY principles:
- **YAGNI**: You Aren't Gonna Need It
- **KISS**: Keep It Simple, Stupid
- **DRY**: Don't Repeat Yourself

For UI work, use `ui-ux-designer` subagent.

**Output:** `✅ Step 2: Implemented [N] files - [X/Y] tasks complete`

---

### Step 3: Testing (100% GATE)

- Write tests covering happy path, edge cases, errors
- Use `tester` subagent to run tests
- If ANY test fails: STOP, use `debugger`, fix, re-run

**FORBIDDEN:**
- Commenting out tests
- Changing assertions to pass
- TODO/FIXME to defer fixes

**Output:** `✅ Step 3: Tests [X/X passed] - All requirements met`

---

### Step 4: Code Review (BLOCKING GATE)

Use `code-reviewer` subagent:
- Check security, performance, architecture
- Return score (X/10), issues list

**If score < 7 or critical issues:**
→ Fix and re-run until approved

**User must explicitly approve to proceed.**

**Output:** `✅ Step 4: Code reviewed - [score]/10 - User approved`

---

### Step 5: Finalize

**After user approval:**
1. Use `project-manager` to update plan status
2. Use `docs-manager` to update documentation
3. Auto-commit with conventional message

**Output:** `✅ Step 5: Finalized - Status updated - Git committed`

---

## Binh Pháp Integration

Before each step, validate WIN-WIN-WIN:
- 👑 ANH (Owner) WIN?
- 🏢 AGENCY WIN?
- 🚀 STARTUP/CLIENT WIN?

---

## Python Integration

```bash
python -c "
from antigravity.core.vibe_workflow import VIBEWorkflow
workflow = VIBEWorkflow()
plan = workflow.detect_plan()
tasks = workflow.analyze_plan()
workflow.print_status()
"
```

---

🏯 **"Công dục thiện kỳ sự, tất tiên lợi kỳ khí"**
*Muốn làm tốt việc gì, trước hết phải có công cụ tốt*
