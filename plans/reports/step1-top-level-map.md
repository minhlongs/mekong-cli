# Step 1: Top-Level Structure Map

**Date:** 2026-08-17
**Repo:** /Users/macbook/mekong-cli
**Scope:** Complete file/directory inventory of ALL top-level directories and key root files

---

## Repository Summary

| Metric | Value |
|--------|-------|
| Total meaningful files (excl. .git, node_modules, .venv, .archive, caches) | 8,242 |
| Total meaningful directories | 1,530 |
| Total meaningful lines (code + docs) | 483,733 |

---

## Top-Level Directory Inventory

### Core Application Code

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `src/` | 1,700 | 121,437 | **Core** | Main Python application: API routes, services, commands, AI agents, billing, DB. Primary codebase. |
| `cli/` | 29 | 2,427 | **Core** | CLI command modules (bridge, content, dashboard, finance, MCP, ops, outreach, revenue, sales). Entry point for user-facing commands. |
| `engine/` | 36 | 3,180 | **Core** | Billing engine: MCU billing, license gate, payments. Core financial logic. |

### Adapter / Integration Layer

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `factory/` | 1 | 89 | **Adapter** | Scaffold template for new modules. Currently near-empty (1 file). |
| `integrations/` | 4 | 126 | **Adapter** | Zalo OA integration only (`zalo.py`). Minimal adapter layer. |
| `cloudflare-skills/` | 0 | 0 | **Adapter** | EMPTY directory. No files. Dead/placeholder. |

### Configuration / Infrastructure

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `recipes/` | 3 | 78 | **Config** | Cloudflare deployment recipes (R2 storage, Workers). Markdown guides. |
| `workflows/` | 3 | 276 | **Config** | Binh-Phap chain, dispatch, ZenOS redesign workflow. Config-driven automation. |
| `observability/` | 11 | 624 | **Infrastructure** | Docker Compose for OTel/Prometheus/PostHog, dashboards, agent metrics. Production monitoring. |
| `config/` | 2 | 80 | **Config** | `cto-config.json` + email sequences. Minimal config files. |
| `dna/` | 5 | 663 | **Config** | Core DNA definitions: command packs, command surface, Binh-Phap operating system, Hermes learning loop. Constitution-layer JSON. |
| `sops/` | 10 | 370 | **Config** | Standard Operating Procedures: business, CEO, engineering, ops, shared. Markdown process docs. |
| `migrations/` | 1 | 181 | **Config** | Single migration script: `fix_model_ids.py`. Database migration. |

### Test / Quality

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `tests/` | 796 | 106,542 | **Tests** | Comprehensive test suite. Largest directory by file count after src/. |
| `evals/` | 1 | 174 | **Tests** | Solo CEO evaluation criteria. Single markdown file. |
| `benchmarks/` | 1 | 444 | **Tests** | Performance baseline Python script. |

### Documentation

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `docs/` | 15 | 4,493 | **Documentation** | Roadmap, changelog, architecture, code standards, harness engineering, VN magic link auth, ZenOS migration guide, command fabric, economic particles. |
| `plans/` | 122 | 10,681 | **Documentation** | Historical plans and reports. Active planning directory. |

### ZenOS / Binh-Phap Layer

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `mekong/` | 150 | 15,292 | **Core (ZenOS)** | Binh-Phap operating system: audit, auth, autopilot, bootstrap, constitution, hooks, init, scripts, skel. Constitution layer. |

### Venture / Business Layer

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `venture-os/` | 84 | 5,970 | **Config (Venture)** | Venture management: ADRs, blueprints, docs, scripts, tools, ventures, workflows. Business strategy layer. |
| `agy-marketplace/` | 0 | 0 | **Dead** | EMPTY directory. No files. Dead/placeholder. |

### Agent Infrastructure

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `agents/` | 1 | 110 | **Config** | Single `registry.yaml` file. Agent registry. |
| `particle/` | 194 | 11,613 | **Core (Particle)** | Self-contained sub-repo with its own `.claude/`, `.git/`, `.github/`, AI workflows. Particle system. |

### Apps / Products

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `apps/` | 144 | 23,406 | **Core (Apps)** | Client applications: api, dashboard, landing, mekong-ide, nhipdieuxanh-orchestrator, sophia-ai-factory. Full-stack Next.js apps. |

### Tooling / Packages

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `packages/` | 4,724 | 70,160 | **Core (Packages)** | Monorepo packages: ask-core, mekong-plugin-sdk, mekong-engine, ui, tooling, agent-sdk, core, memory, mekong-reports, alphaear, + 18 more. Largest directory by line count. |
| `harness/` | 11 | 2,274 | **Core (TypeScript)** | TypeScript harness engine: core, memory, personas, providers. AI agent harness. |
| `scripts/` | 10 | 1,697 | **Core (Scripts)** | Build scripts, demo scripts, migration scripts, shell init. Operational tooling. |

### CI / DevOps

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `.ci/` | 5 | 346 | **Config (CI)** | CI helper scripts: agent/command/skill frontmatter checks, duplicate ClaudeKit checks, Mekong-only primitives. |
| `.github/` | 30 | N/A | **Config (GitHub)** | GitHub Actions workflows (21), issue templates, CODEOWNERS, dependabot, PR templates. Active CI/CD. |
| `.husky/` | 2 | 0 | **Config** | Git hooks (pre-commit). Empty files. |
| `build/` | 2 | 615 | **Config** | Command analysis output (JSON + markdown). Build artifacts. |
| `ci/` | 4 | 201 | **Config (CI)** | Coverage threshold, post-deploy smoke, rollback, run-gate scripts. |

### Orchestration / Agent Runtime

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `.orchestrate/` | 5 | 546 | **Config (Orchestration)** | Build info, execution plans, task plans. Agent orchestration state. |
| `.agents/` | 29 | 2,686 | **Config (Agent Memory)** | Agent handoff files, progress tracking, briefings. Sentinel + teamwork preview agents. |
| `.mekong/` | 12 | 2,388 | **Config (Mekong State)** | Binh-Phap state, company config, audit, events, memory, tool registry, vector index, journal. Runtime state. |
| `.specify/` | 5 | 261 | **Config** | Presets (default, minimal) + templates (plan, spec, tasks). Planning templates. |

### Archives / Caches (Largely Dead)

| Directory | Files | Lines | Classification | Notes |
|-----------|-------|-------|----------------|-------|
| `.archive/` | 279,527 | 103,268 | **Dead (Archive)** | MASSIVE archive: old source, skills, apps, packages, orphan dirs, reports. Should be cleaned or gitignored. |
| `.claude/` | 110,864 | 78,842 | **External (ClaudeKit)** | ClaudeKit agent framework: agents, hooks, skills, worktrees, integration, pipeline, quality. External tooling, not project code. |
| `.codex/` | 1 | 0 | **External (Codex)** | OpenAI Codex config. Single empty file. |
| `.opencode/` | 3 | 32 | **External (OpenCode)** | OpenCode config. External tooling. |
| `.ruff_cache/` | 620 | 0 | **Cache** | Ruff linter cache. Should be gitignored. |
| `.mypy_cache/` | N/A | N/A | **Cache** | MyPy type checker cache. Should be gitignored. |
| `.pytest_cache/` | N/A | N/A | **Cache** | Pytest cache. Should be gitignored. |
| `.turbo/` | 2,510 | 0 | **Cache** | Turborepo cache. Should be gitignored. |
| `.astro/` | N/A | N/A | **Cache** | Astro framework cache. Should be gitignored. |
| `test-results/` | N/A | N/A | **Cache** | Test result artifacts. Should be gitignored. |
| `logs/` | 2 | 0 | **Cache** | Log files. Should be gitignored. |
| `data/` | 1 | 0 | **Data** | Single `algo-trade.db` SQLite database. Data artifact. |
| `models/` | 0 | 0 | **Dead** | EMPTY directory. No files. Dead/placeholder. |
| `plugins/` | 1 | 0 | **Dead** | Single empty file. Dead/placeholder. |

---

## Root-Level File Inventory

### Config / Project Files

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `.gitignore` | 1,423B | **Config** | Git ignore rules |
| `.gitattributes` | 63B | **Config** | Git attributes |
| `.editorconfig` | 266B | **Config** | Editor configuration |
| `.pre-commit-config.yaml` | 449B | **Config** | Pre-commit hooks config |
| `.ruffignore` | 506B | **Config** | Ruff linter ignore rules |
| `.semgrepignore` | 177B | **Config** | Semgrep security scanner ignore |
| `.dockerignore` | 638B | **Config** | Docker ignore rules |
| `.warp_config.json` | 138B | **Config** | Warp terminal config |
| `tsconfig.json` | 911B | **Config** | TypeScript config |
| `turbo.json` | 443B | **Config** | Turborepo config |
| `vitest.config.ts` | 296B | **Config** | Vitest test config |
| `eslint.config.mjs` | 922B | **Config** | ESLint config |
| `Dockerfile` | 768B | **Config** | Main Docker image |
| `Dockerfile.dashboard` | 626B | **Config** | Dashboard Docker image |
| `Dockerfile.seed` | 691B | **Config** | Seed Docker image |
| `docker-compose.yml` | 1.7K | **Config** | Main Docker Compose |
| `docker-compose.seed.yml` | 1.1K | **Config** | Seed Docker Compose |
| `docker-compose.posthog.yml` | 2.9K | **Config** | PostHog Docker Compose |
| `ecosystem.social.cjs` | 1.1K | **Config** | PM2 ecosystem config |
| `requirements.txt` | 631B | **Config** | Python dependencies |
| `requirements.seed.txt` | 62B | **Config** | Seed Python dependencies |

### Environment Files (Sensitive)

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `.env` | 985B | **Config (Sensitive)** | Environment variables. Should NOT be committed. |
| `.env.local` | 227B | **Config (Sensitive)** | Local environment overrides. Should NOT be committed. |
| `.env.test` | 258B | **Config (Sensitive)** | Test environment. Should NOT be committed. |
| `env.example` | 594B | **Config** | Environment template. Safe to commit. |

### Documentation

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `README.md` | 4,934B | **Documentation** | Main project README |
| `CLAUDE.md` | 1,598B | **Documentation** | ClaudeKit engineer context |
| `AGENTS.md` | 4,364B | **Documentation** | Agent definitions |
| `AGY.md` | 777B | **Documentation** | AGY (Alternate GitHub YAML?) config |
| `SECURITY.md` | 1,568B | **Documentation** | Security policy |
| `TEST_INFRA.md` | 18,747B | **Documentation** | Test infrastructure documentation |
| `TEST_READY.md` | 1,064B | **Documentation** | Test readiness checklist |
| `ZENOS.md` | 9,575B | **Documentation** | ZenOS philosophy/constitution |
| `VERSION` | 6B | **Documentation** | Version file |

### CLI / Agent Config

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `.claudeignore` | 125B | **Config (ClaudeKit)** | ClaudeKit ignore rules |
| `.cursorrules` | 518B | **Config (Cursor)** | Cursor editor rules |
| `.fable-5` | 831B | **Config (fable-5)** | fable-5 ignore rules |

### Python Scripts (Root-Level) -- LIKELY DEAD/ORPHANED

| File | Size | Classification | Rationale |
|------|------|----------------|-----------|
| `apply_all_fixes.py` | 38,838B | **Dead** | One-shot fix script. Applied fixes historically. No longer needed. |
| `apply_all_fixes_v2.py` | ~same | **Dead** | V2 of above. Same status. |
| `fix_indent.py` | 1.3K | **Dead** | Indentation fix script. One-time use. |
| `fix_security.py` | 5.6K | **Dead** | Security fix script. One-time use. |
| `reapply_fixes.py` | 38,838B | **Dead** | Reapply fixes script. One-time use. |
| `verify_brand.py` | 37B | **Dead** | Brand verification script. One-time use. |
| `conftest.py` | ~small | **Core (Test)** | Pytest conftest. Active test infrastructure. |
| `di_container.py` | ~small | **Core** | Dependency injection container. Potentially active. |

### Build / Validation Scripts

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `run_validation.sh` | 1,162B | **Config (CI)** | Validation runner script |
| `run_validation.log` | 78,341B | **Dead** | Validation log output. Should be gitignored. |
| `stack.patch` | 46B | **Dead** | Empty/near-empty patch file. |

### Data Files

| File | Size | Classification | Notes |
|------|------|----------------|-------|
| `usage_2026-03-09_current.json` | 18B | **Dead** | Usage snapshot from March 2026. Stale data. |

---

## .bak / Legacy Files Found

| Location | Files | Classification | Notes |
|----------|-------|----------------|-------|
| `src/commands/license_admin.py.bak2` | 1 | **Dead** | Backup of license admin. Legacy. |
| `src/commands/license_admin.py.bak3` | 1 | **Dead** | Backup of license admin. Legacy. |
| `src/commands/license_admin.py.bak4` | 1 | **Dead** | Backup of license admin. Legacy. |
| `cli/main.py.new` | 1 | **Dead** | New version of main CLI. Staged but not applied. |

Note: Multiple copies of these `.bak` files exist inside `.claude/worktrees/` (worktree copies), but the canonical ones are in `src/commands/`.

---

## Key Observations

1. **Massive archive debt**: `.archive/` contains 279,527 files / 103,268 lines of dead code. This is the single largest directory by file count and should be evaluated for removal.

2. **ClaudeKit bloat**: `.claude/` contains 110,864 files / 78,842 lines. This is external tooling state, not project code, but inflates repo size significantly.

3. **Root Python scripts are dead**: All 6 root-level `fix_*.py` / `apply_*.py` / `verify_*.py` scripts are one-time repair scripts that should be deleted or moved to `.archive/`.

4. **Empty placeholder directories**: `cloudflare-skills/`, `agy-marketplace/`, `models/` are all empty. `plugins/` has only an empty file. These are dead placeholders.

5. **Sensitive files at root**: `.env`, `.env.local`, `.env.test` appear to be committed. Verify these are not leaking secrets.

6. **Stale data files**: `run_validation.log` (78KB), `usage_2026-03-09_current.json`, `stack.patch` are artifacts that should be gitignored.

7. **`packages/` is the largest code directory**: 4,724 files / 70,160 lines. This is a monorepo with 28+ packages. The harness engine and particle system live here.

8. **`src/` is the primary Python codebase**: 1,700 files / 121,437 lines. Contains API routes, services, commands, AI agents, billing, DB.

9. **`tests/` is comprehensive**: 796 files / 106,542 lines. Good test coverage.

10. **`mekong/` is the ZenOS constitution layer**: 150 files / 15,292 lines. Binh-Phap operating system with auth, autopilot, bootstrap, constitution, hooks, init, scripts, skel.

---

## Classification Legend

- **Core**: Active application code, essential to the product
- **Adapter**: Integration/scaffold code that bridges external systems
- **Config**: Configuration, documentation, process definitions
- **Dead**: Empty directories, one-time scripts, stale data, legacy backups
- **Orphan**: Files that exist but have no clear owner or purpose
- **External**: External tooling state (ClaudeKit, Codex, etc.) not part of project code
- **Infrastructure**: Production monitoring, deployment, CI/CD
- **Cache**: Runtime caches that should be gitignored
- **Tests**: Test suites and evaluation criteria
