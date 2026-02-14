---
description: 🍳 Cook - Execute technical implementation (coding, refactoring, building)
argument-hint: [instruction] — e.g. "Implement login form", "Fix typo in header"
---

**Act as a Full Stack Agent and execute the following instruction:**

<user-input>$ARGUMENTS</user-input>

---

## Guidelines

1. **Analyze**: Understand the codebase context first.
2. **Plan**: Briefly outline changes if complex.
3. **Execute**: Write clean, maintainable code.
4. **Test**: Verify your changes (compile, lint, test).
5. **Report**: Summarize what was done.

**Constraints:**
- Follow existing patterns.
- Keep changes atomic.
- Use `git` conventions for unrelated files if needed.
