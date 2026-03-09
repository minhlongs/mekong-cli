# Phase 1: Dọn Rác Root — Loại Bỏ Rogue Files

## Overview
- **Ưu tiên:** P0 CRITICAL
- **Trạng thái:** TODO
- **Mô tả:** Xóa/di chuyển các file rác ở root level. Root chỉ nên có config files + README.

## Phân Tích Hiện Tại

### Files Rác Ở Root (PHẢI xóa/di chuyển)

| File | Kích thước | Hành động |
|------|-----------|----------|
| `repomix-output.xml` | **83MB** | XÓA — generated output |
| `tom_hum_vibe.log` | 1.4MB | XÓA — runtime log |
| `build_full_log.txt` | 56KB | XÓA — build artifact |
| `build_full_log_v2.txt` | 20KB | XÓA — build artifact |
| `build_log.txt` | ~1KB | XÓA |
| `build_log_filtered.txt` | ~0.2KB | XÓA |
| `build_log_full.txt` | ~0.9KB | XÓA |
| `build_log_full_v2.txt` | 30KB | XÓA |
| `test_output.txt` | 72KB | XÓA — test artifact |
| `team_test_output.txt` | 452KB | XÓA — test artifact |
| `coverage_full.txt` | 12KB | XÓA — coverage artifact |
| `coverage_report.txt` | 85KB | XÓA — coverage artifact |
| `ts_prune_output.txt` | 2KB | XÓA |
| `circular_deps.txt` | 0 | XÓA — empty |
| `dead_code.txt` | 0 | XÓA — empty |
| `src_dead_code.txt` | 0 | XÓA — empty |
| `madge_output.txt` | ~0.2KB | XÓA |
| `adapter.log` | ~0.7KB | XÓA — runtime log |
| `test.db` | 0 | XÓA — test artifact |
| `usage_2026-03-09.json` | ~0.02KB | XÓA — runtime data |
| `test_fetch.js` | ~0.4KB | DI CHUYỂN → `tests/` hoặc XÓA |
| `test_input.jsonl` | ~0.2KB | DI CHUYỂN → `tests/` hoặc XÓA |
| `test-keys.mjs` | ~0.2KB | DI CHUYỂN → `tests/` hoặc XÓA |
| `test-pkg-import.mjs` | ~0.1KB | DI CHUYỂN → `tests/` hoặc XÓA |
| `check-dist.mjs` | ~0.2KB | DI CHUYỂN → `scripts/` |
| `Patterns` | 0 | XÓA — empty |
| `agencyos.db` | 24KB | XÓA — sqlite artifact |
| `poetry.lock.backup` | 306KB | XÓA — backup file |
| `uv.lock` | ~0.05KB | XÓA — unused |

### Files Hợp Lệ Ở Root (GIỮ)

```
CLAUDE.md, GEMINI.md, README.md, README.vi.md
CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, AGENTS.md
LICENSE, VERSION, Makefile
package.json, pnpm-lock.yaml, pnpm-workspace.yaml
pyproject.toml, poetry.lock, conftest.py, pytest.ini
tsconfig.json, tsconfig.base.json, turbo.json, vitest.config.ts
.gitignore, .gitmodules, .gitattributes, .gitbook.yaml
.coveragerc, .dockerignore, .editorconfig, .eslintignore
.env, .env.example (+ variants)
.npmrc, .python-version, .mcp.json
.pre-commit-config.yaml, .ruffignore, .cursorrules, .geminiignore
```

### Hidden Dirs Cần Đánh Giá

| Dir | Files | Hành động |
|-----|-------|----------|
| `.ag_proxies/` | ? | Đánh giá — có thể legacy |
| `.agencyos/` | ? | Đánh giá — legacy AgencyOS |
| `.agent/` | ? | GIỮ nếu đang dùng |
| `.antigravity/` | ? | GIỮ — telemetry/memory |
| `.archive/` | ? | GIỮ — archived data |
| `.claude-flow/` | ? | Đánh giá — có thể legacy |
| `.claude-skills/` | ? | Đánh giá — có conflict với .claude/skills? |
| `.clawhub/` | ? | Đánh giá |
| `.cleo/` | ? | GIỮ — Cleo task management |
| `.entire/` | ? | Đánh giá |
| `.git_backup_sophia/` | ? | XÓA — git backup |
| `.husky/` | ? | GIỮ — git hooks |
| `.logs/` | ? | XÓA — runtime logs |
| `.mekong/` | ? | GIỮ — project config |
| `.opencode/` | ? | Đánh giá |
| `.playwright-mcp/` | ? | Đánh giá |
| `.swarm/` | ? | Đánh giá |
| `.taskmaster/` | ? | Đánh giá — legacy? |
| `.tom_hum_state.json` | 1 file | DI CHUYỂN vào apps/openclaw-worker/ |
| `.turbo/` | ? | GIỮ — Turborepo cache |
| `.warp_config.json` | 1 file | Đánh giá |
| `.workflow-migration-backup-*` | ? | XÓA — migration backup |

## Implementation Steps

1. Thêm vào `.gitignore`:
   ```
   # Build/test artifacts
   *.log
   *_output.txt
   *_log*.txt
   coverage_*.txt
   repomix-output.xml
   *.db
   usage_*.json
   ```

2. Xóa files rác (1 commit):
   ```bash
   git rm --cached repomix-output.xml tom_hum_vibe.log build_*.txt \
     test_output.txt team_test_output.txt coverage_*.txt \
     ts_prune_output.txt circular_deps.txt dead_code.txt src_dead_code.txt \
     madge_output.txt adapter.log test.db usage_*.json Patterns \
     agencyos.db poetry.lock.backup uv.lock
   ```

3. Di chuyển test files:
   ```bash
   git mv test_fetch.js tests/fixtures/
   git mv test_input.jsonl tests/fixtures/
   git mv test-keys.mjs tests/fixtures/
   git mv test-pkg-import.mjs tests/fixtures/
   git mv check-dist.mjs scripts/
   ```

4. Di chuyển `.tom_hum_state.json` → `apps/openclaw-worker/`

5. Xóa hidden dirs legacy:
   ```bash
   rm -rf .git_backup_sophia .workflow-migration-backup-*
   git rm -r .logs
   ```

## Todo List

- [ ] Cập nhật `.gitignore`
- [ ] `git rm` các files rác
- [ ] Di chuyển test fixtures
- [ ] Di chuyển `.tom_hum_state.json`
- [ ] Xóa hidden dirs legacy
- [ ] Chạy `python3 -m pytest` để verify
- [ ] Commit: `refactor(root): dọn rác root level — xóa 83MB artifacts, cập nhật gitignore`

## Success Criteria

- Root level chỉ còn config files, README, và workspace files
- Không còn build/test artifacts ở root
- `.gitignore` ngăn tái phát
- Tests pass
