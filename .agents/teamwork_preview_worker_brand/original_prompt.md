## 2026-05-28T09:20:42Z

You are a teamwork_preview_worker.
Your working directory is `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand/`.
Your task is to write and configure the brand identity system and visual assets for the "Nhịp Điệu Xanh" platform in `/Users/macbook/nhipdieuxanh-agent/brand` by copying or using the designs proposed by the explorers.

Steps:
1. Create the directories `/Users/macbook/nhipdieuxanh-agent/brand` and `/Users/macbook/nhipdieuxanh-agent/brand/logos` if they do not exist.
2. Read `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_brand_1/proposed_brand_tokens.json` and save its contents to `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json`.
3. Copy or recreate the SVG files from `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_brand_2/` to the `/Users/macbook/nhipdieuxanh-agent/brand/logos/` directory:
   - `proposed_logo-primary.svg` -> `logo-primary.svg`
   - `proposed_logo-monochrome.svg` -> `logo-monochrome.svg`
   - `proposed_logo-symbol.svg` -> `logo-symbol.svg`
   - `proposed_favicon.svg` -> `favicon.svg`
4. Read `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_brand_3/proposed_guidelines.html` and write it to `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html`.
5. Run the verification checks:
   - Check if all files exist and are at least 100 bytes.
   - Run a Python script or similar command to check that the SVG files are valid XML documents.
   - Run a Python script or Node script to parse `brand_tokens.json` and verify its valid JSON format.
6. Write a complete handoff report in your agent directory `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand/handoff.md` detailing the actions taken, exact file paths created, and the execution/output of the verification commands.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
