# Original Prompt

## 2026-05-28T07:16:50Z

You are the Project Orchestrator for the Sophia AI Factory codebase verification task.
Your working directory for metadata (plan.md, progress.md, etc.) is `/Users/macbook/mekong-cli/.agents/orchestrator_sophia_verification/`.

The user request is located in `/Users/macbook/mekong-cli/ORIGINAL_REQUEST.md`.

Your goal is to run comprehensive codebase quality checks (/code) and verification on the Sophia AI Factory repository at `/Users/macbook/projects/sophia-ai-factory`.

Please decompose this project into clear milestones:
1. Static Analysis Verification: Compile without type-safety errors (tsc) and lint errors (eslint) in `apps/sophia-ai-factory`.
2. Test Suite Completion: Ensure all unit and integration tests inside `apps/sophia-ai-factory` run and pass.
3. Production Build Validation: Ensure Next.js builds successfully under Cloudflare wrangler/opennextjs setup.

Follow the Binh Pháp framework:
- Decompose, write plan.md and progress.md in your working directory.
- Spawn specialist subagents (e.g. explorer, worker/implementer, reviewer) to analyze, remediate any errors, and verify the builds.
- Run checks, fix lints/types if needed, run vitest, run next.js build.
- Write handoff.md in your directory when complete.
