# Planner Report — Mekong CLI AGI Go Live

**Ngày:** 2026-02-27 | **Plan dir:** `plans/260227-2145-mekong-cli-agi-go-live/`

## Tóm tắt

Đã tạo implementation plan 5 phases đưa mekong-cli từ internal tool (75% CLI + 70% infra) lên production-ready public AGI CLI platform. Tổng effort ước tính: **16h**.

## Phases

| # | Phase | Effort | Priority | Blockers |
|---|-------|--------|----------|----------|
| 1 | Fix Critical Blockers | 4h | P0 | Gateway tests, PayPal, port, .env |
| 2 | Code Quality & Refactor | 4h | P1 | 3 files >200 LOC |
| 3 | Package & Publish | 3h | P1 | PyPI + npm publish setup |
| 4 | CI/CD Hardening | 3h | P1 | Smoke test, Docker optimize |
| 5 | Docs & Launch | 2h | P1 | README, CONTRIBUTING, release |

## Dependency Graph

Phase 1 → {Phase 2, Phase 3, Phase 4} (song song) → Phase 5 → Release v2.2.0

## Key Decisions

- Port proxy: **9191** (ĐIỀU 56), port 20128 = openclaw engine mode riêng
- Package name: `mekong-cli` (đổi từ `mekong-cli-lean`)
- Payment: Polar.sh only — xóa toàn bộ PayPal
- V1 scope: CLI engine + openclaw-worker + packages/core + packages/agents

## Files tạo

- `plans/260227-2145-mekong-cli-agi-go-live/plan.md`
- `plans/260227-2145-mekong-cli-agi-go-live/phase-01-fix-critical-blockers.md`
- `plans/260227-2145-mekong-cli-agi-go-live/phase-02-code-quality-refactor.md`
- `plans/260227-2145-mekong-cli-agi-go-live/phase-03-package-publish.md`
- `plans/260227-2145-mekong-cli-agi-go-live/phase-04-cicd-hardening.md`
- `plans/260227-2145-mekong-cli-agi-go-live/phase-05-docs-public-launch.md`

## Unresolved Questions

1. GitHub Secrets (`GCP_SA_KEY`, `NPM_TOKEN`, `PYPI_TOKEN`) đã cấu hình chưa?
2. `bin/oc` entry point — ship public hay internal only?
3. PyPI name `mekong-cli` có bị taken chưa? Cần check trước publish.
