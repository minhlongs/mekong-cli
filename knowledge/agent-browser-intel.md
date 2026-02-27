# Agent Browser Context Reduction Protocol (Sinh Gián)
Date: 2026-02-23

## Status
- **Installation**: Configured via the official Playwright CC CLI plugin since the custom `agent-browser` npm package was unavailable.
- **Skill Wrapper**: `agent-browser` SKILL created at `.claude/skills/agent-browser/SKILL.md`.

## Context Reduction Pattern (93% Savings)
The custom `agent-browser` skill wrapper establishes standard rules for Claude CLI to avoid consuming too many tokens when scraping raw HTML pages:
1. **Filter Scripts/Styles**: Instructs Playwright to only evaluate DOM without `<script>` and `<style>` tags.
2. **Text-Only Extraction**: Emphasizes `innerText` or the standard accessibility tree over complete HTML dumps.
3. **Mưu Kế (Sinh Gián)**: Mắt luôn theo sát mục tiêu (browser automation) qua chụp ảnh screenshot (base64) để "nhìn" thay vì "đọc code HTML".

## Integration
Commands available to agents: `@open`, `@click`, `@type`, `@snapshot`. They act as pseudo-macros that map directly to underlying Playwright capabilities within CC CLI sessions.
