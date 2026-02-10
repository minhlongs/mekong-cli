---
description: 🚀 Quick code — Direct fullstack-developer agent delegation with auto skill activation
argument-hint: [task-description]
---

**Ultrathink** and implement the following coding task immediately using Agent Teams:

<task>$ARGUMENTS</task>

---

## Execution Protocol

1. **Read Context**: Scan `CLAUDE.md`, `./docs/`, and relevant source files
2. **Activate Skills**: Match task keywords to `.claude/skills/` catalog:
   - Frontend → `frontend-development`, `react-best-practices`, `ui-styling`
   - Backend → `backend-development`, `databases`
   - API → `web-frameworks`
   - DevOps → `devops`
   - AI → `ai-multimodal`, `google-adk-python`
3. **Implement**: Use `fullstack-developer` subagent for core implementation
4. **Type-Check + Build**: Run compile/build command to verify no errors
5. **Quick Test**: Use `tester` subagent for critical path tests
6. **Report**: Brief summary of changes + any issues found

## Rules

- Follow YAGNI/KISS/DRY principles
- Modularize files >200 lines
- Use kebab-case naming with descriptive names
- Type hints required for all functions
- Run build verification before reporting done
- **IMPORTANT:** Sacrifice grammar for concision in reports
