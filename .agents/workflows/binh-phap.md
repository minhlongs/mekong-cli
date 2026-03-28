---
description: "⚔️ Binh Pháp strategic execution framework. Actions: plan → implement → verify → ship."
---

# /binh-phap — Strategic Execution Framework

**AUTO-EXECUTE MODE.** Detect action from user prompt. Execute without asking clarifying questions.

## Actions

### `plan` — 第一篇 始計 (Strategic Planning)

1. Analyze the task deeply:
   - Scan relevant codebase areas
   - Check dependencies and potential conflicts
   - Assess risks
2. Create implementation plan in `./plans/` directory
3. Follow progressive disclosure: `plan.md` overview → `phase-XX-*.md` details
4. Present plan with pros/cons to user for approval
5. **Do NOT implement** until user approves

### `implement` — 第七篇 軍爭 (Parallel Execution)

1. Read the latest approved plan from `./plans/` directory
2. Execute implementation:
   - Core code implementation
   - Frontend/UI changes (if applicable)
   - Write tests alongside code
3. Run type-check + build after each phase
4. Follow Plan-Execute-Verify cycle

### `verify` — 第十一篇 九地 (Verification)

**KHÔNG TIN BÁO CÁO - PHẢI XÁC THỰC!**

1. Run full test suite
2. Debug any failures found
3. Check production site via browser if deployed
4. Report verification results with evidence (screenshots/logs)

### `ship` — 第十二篇 火攻 (Deploy)

1. Final code review for quality and security
2. Update documentation if needed
3. Commit with convention:
   ```
   feat: [module] - Description
   fix: [module] - Description
   ```
4. Deploy if applicable, then verify production

## Rules

- Always read project README/docs first for context
- Reports must be concise — sacrifice grammar for brevity
- Verification is MANDATORY before shipping
