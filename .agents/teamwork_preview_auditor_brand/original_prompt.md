## 2026-05-28T09:48:32Z
You are acting as the Forensic Auditor (teamwork_preview_auditor).
Your working directory is `/Users/macbook/mekong-cli/.agents/teamwork_preview_auditor_brand/`.
Your task is to perform an integrity audit on the brand identity assets generated for the 'Nhịp Điệu Xanh' brand under `/Users/macbook/nhipdieuxanh-agent/brand`.

You must perform the following checks:
1. Parse `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json` to verify it is valid JSON and contains genuine data (no hardcoded test bypasses or dummies).
2. Parse all SVG logo files in `/Users/macbook/nhipdieuxanh-agent/brand/logos/` (logo-primary.svg, logo-monochrome.svg, logo-symbol.svg, favicon.svg) to verify they are valid XML and contain valid SVG paths.
3. Check `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html` to verify it is valid HTML, links stylesheets/fonts, and contains color grids, font scales, inline SVGs, and rules.
4. Perform case-insensitive searches across all files in the brand folder for forbidden keywords (OpenClaw, mekong-cli, RaaS, Water Protocol) to ensure there are no remnants of boilerplate templates.
5. Verify that `logo-symbol.svg` has correct stroke outlines on the overlapping elements.
6. Check for any dummy implementations, cheats, or bypasses.
7. Provide a clear, binary verdict: CLEAN or VIOLATION.

Write your final audit report to `/Users/macbook/mekong-cli/.agents/teamwork_preview_auditor_brand/handoff.md` and send a message back with the verdict and summary.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
