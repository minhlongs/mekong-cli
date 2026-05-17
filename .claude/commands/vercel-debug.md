---
description: "Debug Vercel CI/CD deployments — check status, fix errors, verify production GREEN"
argument-hint: [deployment-url or omit for interactive]
why-override: "Mekong has the verification-loop variant (5-step debug + GREEN gate). Global /vercel-debug at ~/.claude/commands is the older 'no-frontmatter' rules-only doc."
---

# /vercel-debug — Vercel CI/CD Debugging Workflow

Debug and recover Vercel deployments. Follow verification loop until production GREEN.

## Instructions

### 1. Check Vercel Status

```bash
vercel ls --yes 2>&1 | head -20
```

### 2. If any deployment shows ERROR

```bash
vercel inspect <deployment-url> 2>&1
vercel logs <deployment-url> 2>&1 | tail -100
```

### 3. Fix Errors Locally

- Read error message carefully
- Fix the issue in source code
- Test locally: `npm run build`

### 4. Redeploy (via git push — NEVER vercel --prod)

```bash
git push origin main
# GitHub Actions → Vercel auto-deploys
```

### 5. VERIFICATION LOOP (MANDATORY)

**DO NOT STOP until:**

- [ ] CI/CD GitHub Actions shows "success"
- [ ] Build logs show no errors
- [ ] Live site loads successfully (HTTP 200)
- [ ] All console errors cleared

### 6. Report Format

```
Build: ✅/❌ | Tests: ✅/❌ | CI/CD: ✅/❌ | Production: ✅/❌ HTTP [code]
```

---

## CC CLI Input Rule (CRITICAL)

See `.claude/rules/cc-cli-input-rules.md` — Input MUST end with `\n`.

---

## Error Recovery Loop

```
while deployment_status != "Ready":
    1. Get error logs
    2. Fix locally
    3. Build locally (npm run build)
    4. git push → auto-deploy
    5. Poll CI/CD until complete
    6. Verify production HTTP 200
```

## Related Commands

- `/deploy` — Standard deployment workflow
- `/health` — Infrastructure health check
- `/cloudflare` — Cloudflare Workers deployment

---

*Ported from claudekit ~/.claude/commands/vercel-debug.md — 2026-04-16*
