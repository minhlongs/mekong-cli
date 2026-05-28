---
name: portfolio-status
description: Generate portfolio status report for projects in the monorepo. Scans deployment status, recent commits, health checks, and business metrics.
---

# Portfolio Status Report Generator

## When to Use
When asked to generate a portfolio status report, project health check, or deployment summary.

## Steps
1. Scan recent git commits across the monorepo
2. Check deployment status for each active project (Cloudflare Pages, Vercel)
3. Review open issues and PRs
4. Generate a structured report with PASS/FAIL for each project
5. Save report to `plans/reports/portfolio-status-YYMMDD.md`

## Output Format
```markdown
# Portfolio Status Report — [DATE]

| Project | Deployed | Last Commit | Health | Notes |
|---------|----------|-------------|--------|-------|
| wellnexus | ✅ | ... | OK | ... |
| algo-trader | ✅ | ... | OK | ... |
| sophia | ✅ | ... | OK | ... |
```
