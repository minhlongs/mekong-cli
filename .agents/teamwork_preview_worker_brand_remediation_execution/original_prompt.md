## 2026-05-28T09:36:35Z

You are a teamwork_preview_worker.
Your working directory is `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand_remediation_execution/`.
Your task is to execute the staged brand remediation script to fix the boilerplate and outline issues on the brand assets, and run checks to verify success.

Steps:
1. Run the remediation script:
   `python3 /Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand_remediation/remediate.py`
2. If it succeeds, verify the following files in `/Users/macbook/nhipdieuxanh-agent/brand` to make sure they are updated correctly:
   - Check `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json` (ensure no "OpenClaw" or "mekong-cli" references exist).
   - Check `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html` (ensure it has no references to "OpenClaw", "mekong-cli", "RaaS", or "Water Protocol").
   - Check that `/Users/macbook/nhipdieuxanh-agent/brand/logos/logo-symbol.svg` has stroke and white outline elements for separation.
3. If the script fails, analyze the error and fix the files directly.
4. Output a detailed handoff report in your directory `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_brand_remediation_execution/handoff.md` detailing the script execution, its output, and your verification findings.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
