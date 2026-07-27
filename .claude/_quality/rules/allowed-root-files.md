# Allowed Root Files

Files and directories permitted at the mekong-cli project root. Everything else should be moved to `.archive/` or a subdirectory.

## Source/Config
- `CLAUDE.md` — project instructions
- `ZENOS.md` — constitutional document
- `README.md` — project overview
- `VERSION` — version stamp
- `package.json` — npm package manifest
- `package-lock.json` — npm lock file (xor pnpm-lock.yaml)
- `pnpm-lock.yaml` — pnpm lock file (xor package-lock.json)
- `pnpm-workspace.yaml` — pnpm workspace config
- `tsconfig.json` — TypeScript config
- `turbo.json` — Turborepo config
- `vitest.config.ts` — Vitest config
- `pyproject.toml` — Python project config
- `pytest.ini` — pytest config
- `requirements.txt` — Python dependencies
- `conftest.py` — pytest fixtures
- `.editorconfig` — editor settings
- `.pre-commit-config.yaml` — pre-commit hooks
- `.gitattributes` — git attributes
- `.gitignore` — git ignore rules
- `.repomixignore` — repomix ignore rules
- `.ruffignore` — ruff/rules linting ignore
- `.sentryclirc` — Sentry CLI config
- `.geminiignore` — Gemini CLI ignore rules
- `Dockerfile` — Docker build
- `Dockerfile.dashboard` — Dashboard Docker build
- `Makefile` — build targets
- `docker-compose.yml` — Docker Compose
- `docker-compose.posthog.yml` — PostHog Docker Compose
- `ecosystem.social.cjs` — PM2 ecosystem

## Metadata
- `LICENSE` — MIT license
- `CODE_OF_CONDUCT.md` — code of conduct
- `CONTRIBUTING.md` — contribution guide
- `SECURITY.md` — security policy
- `GEMINI.md` — Gemini CLI docs
- `ANTIGRAVITY.md` — Antigravity docs
- `ARCHITECTURE.md` — architecture docs
- `QUICKSTART.md` — quickstart guide
- `release-manifest.json` — release manifest
- `opencode.json` — OpenCode config

## Directories (explicitly permitted)
- `.claude/` — Claude CLI config
- `.mekong/` — Mekong engine state
- `.github/` — GitHub config
- `.husky/` — Git hooks
- `.archive/` — archived files
- `mekong/` — Mekong engine
- `scripts/` — shell/node scripts
- `packages/` — workspace packages
- `recipes/` — command recipes
- `docs/` — documentation
- `tests/` — test suite
- `src/` — source code
- `apps/` — application packages (PRIVATE, NOT committed)
- `core/` — core modules
- `cli/` — CLI commands
- `services/` — service definitions
- `api/` — API routes
- `plans/` — plan documents
- `reports/` — generated reports
- `config/` — configuration
- `data/` — data files
- `logs/` — log output
- `bootstrap/` — bootstrap scripts
- `examples/` — example code
- `factory/` — factory contracts
- `clipmart/` — marketplace templates
- `models/` — ML models
- `ci/` — CI config
- `landing/` — landing pages
- `marketing/` — marketing assets
- `content/` — content assets
- `controllers/` — API controllers
- `contracts/` — contract definitions
- `integrations/` — third-party integrations
- `build/` — build output
- `invoices/` — invoice templates
- `newsletter-saas/` — newsletter SaaS
- `templates/` — templates
- `tenants/` — tenant configs
- `workflows/` — workflow definitions
- `proposals/` — proposals
- `antigravity/` — Antigravity integration
- `claude_bridge/` — Claude bridge
- `cloudflare-skills/` — Cloudflare skills
- `ide-core/` — IDE core
- `plugins/` — plugins
- `particle/` — Particle subproject
- `zenos-test/` — ZenOS test subproject
- `test-particle/` — test particle subproject

## Not Allowed at Root (must be in `.archive/` or subdirectory)
- `.agent/` — agent runtime data
- `.agents/` — agent definitions
- `.antigravity/` — Antigravity runtime
- `.gemini/` — Gemini CLI runtime
- `.opencode/` — OpenCode runtime
- `.cursorrules` — Cursor rules
- `.claude-backup/` — Claude backup
- `.claude-skills/` — Claude skills backup
- Stale reports: `GO_LIVE_REPORT.md`, `STRATEGY.md`, `PHASE*`, `repomix-output.xml`, etc.
