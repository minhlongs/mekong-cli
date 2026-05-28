## 2026-05-28T09:28:19Z
You are a teamwork_preview_worker.
Your working directory is `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand_remediation/`.
Your task is to remediate the brand identity assets in `/Users/macbook/nhipdieuxanh-agent/brand` based on the critical review feedback.

Review Feedback to Address:
1. **brand_tokens.json**:
   - Change descriptions to refer to the "Nhịp Điệu Xanh" brand instead of "mekong-cli" and its "Water Protocol".
   - Modify line 7 primary color description to represent growth, sustainability, renewable energy, and ecological balance.
   - Modify line 108 accent description to represent digital CRM touchpoints, active states, and interactive focus states for Nhịp Điệu Xanh.
2. **guidelines.html**:
   - Change all references of "OpenClaw RaaS Gateway" and "OpenClaw" to "Nhịp Điệu Xanh".
   - Change descriptions and values. Replace RaaS values (Speed, Security, Adaptability) with Nhịp Điệu Xanh values: e.g. Sustainability (Emerald), Precision & CRM Ergonomics (Teal), and Trust & Warmth (Amber).
   - In the logo showcase section, replace the inline "OpenClaw" logos (which have the cross icon and "OpenClaw" text) with the actual "Nhịp Điệu Xanh" SVG logos (Primary, Monochrome, Symbol, Favicon) and "Nhịp Điệu Xanh" text.
   - Ensure the inline SVGs in `guidelines.html` match the exact SVG code of `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-primary.svg`, `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-monochrome.svg`, and `/Users/macbook/nhipdieuxanh-agent/brand/logos/favicon.svg`.
   - Update the footer to "© 2026 Nhịp Điệu Xanh. All rights reserved." and remove the BSL 1.1 license reference.
3. **logos/logo-symbol.svg**:
   - Add a white outline separator to the house path and rhythm wave path (such as `stroke="#FFFFFF" stroke-width="2"`) so they do not bleed into the green and teal leaf wings when rendered on colored or transparent backgrounds. This makes it consistent with `logo-primary.svg`.

Verification Steps:
- Verify that no occurrences of "OpenClaw" or "mekong-cli" remain in `brand_tokens.json` and `guidelines.html`.
- Run a Python script or similar parser command to check that the SVG files are valid XML documents.
- Run a Python script or Node script to parse `brand_tokens.json` and verify its valid JSON format.
- Document all file edits and verification command outputs in your handoff report at `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand_remediation/handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
