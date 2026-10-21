---
name: stitch-loop
description: >-
  Autonomous multi-page frontend build loop using Google Stitch MCP API and baton relay files. Orchestrates continuous screen generation, verification, and sitemap synchronization.
---

# /stitch-loop — Continuous Stitch Generation Loop

Autonomous multi-page frontend build loop powered by Google Stitch MCP API (`https://stitch.googleapis.com/mcp`) and baton relay pattern.

## Workflow
1. Read current generation baton from `next-prompt.md`.
2. Dispatch prompt with Section 6 design tokens to Google Stitch MCP API (`generate_screen_from_text`).
3. Download HTML and screenshot to `queue/[page].html` and `queue/[page].png`.
4. Integrate page into `site/public/` with global cyber navbar and `Cmd+K` palette.
5. Update `SITE.md` sitemap with `[x]` and 32-char Stitch Screen ID.
6. Advance `next-prompt.md` to next baton target so the pipeline never stalls.

## Execution
```bash
python3 scripts/verify_site_public.py
```
