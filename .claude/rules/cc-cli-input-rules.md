# CC CLI Input Rules - MANDATORY GLOBAL RULES

## 🔴 RULE #1: ALWAYS ADD NEWLINE

When using `send_command_input` tool to send input to Claude Code CLI:

```
THE INPUT PARAMETER MUST ALWAYS END WITH \n
```

### Examples

| Scenario         | WRONG ❌         | CORRECT ✅         |
| ---------------- | ---------------- | ------------------ |
| Confirm yes      | `"yes"`          | `"yes\n"`          |
| Select option 1  | `"1"`            | `"1\n"`            |
| Select option 2  | `"2"`            | `"2\n"`            |
| Send empty enter | `""`             | `"\n"`             |
| Multi-line       | `"commit\npush"` | `"commit\npush\n"` |

### Why This Matters

Without `\n`, the CC CLI waits for Enter key which never comes:

- Command hangs indefinitely
- User has to manually intervene
- Workflow breaks
- Time wasted

### Before Every `send_command_input` Call

**CHECKLIST:**

1. [ ] Does Input end with `\n`?
2. [ ] Is WaitMs sufficient? (30000-60000 for most operations)
3. [ ] Is SafeToAutoRun set appropriately?

---

## 🔴 RULE #2: VERIFICATION LOOP

After ANY deployment/push:

1. Check build status
2. Check deployment logs
3. Verify live site works
4. **DO NOT STOP** until 100% green

---

## 🔴 RULE #3: ERROR RECOVERY

If deployment fails:

1. Get exact error from logs
2. Fix locally
3. Test build locally: `npm run build`
4. Redeploy
5. Verify again
6. Repeat until GREEN
