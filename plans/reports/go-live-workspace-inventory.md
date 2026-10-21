# Go-live workspace inventory

Generated: 2026-10-18 (local worktree snapshot)
Branch: `feat/trade-transport-remedies-suite-phases-163-166`

This inventory uses `git status --untracked-files=all` and includes staged, unstaged, deleted, and every non-ignored untracked file. It does not stage, commit, or discard workspace content.

## Counts

- Git status paths: **2102**.
- Status classes: `{' D': 11, ' M': 624, '??': 1464, 'D ': 3}`.
- Every path remains preserved in the working tree; the release disposition is a selection guide, not an automatic filter.

## Classification

| Classification | Entries |
|---|---:|
| `asset` | 11 |
| `build_or_runtime_config` | 20 |
| `data_or_dependency_input` | 6 |
| `documentation` | 258 |
| `generated_or_cache` | 2 |
| `generated_or_local_output` | 17 |
| `manual_review` | 2 |
| `source` | 1683 |
| `test` | 103 |

Classification is path-based and needs owner review for ambiguous assets/data. The `site/public/app/` output is classified separately because the Pages workflow deploys from `site/public/`.

## Largest top-level groups

| Path | Entries |
|---|---:|
| `src` | 1308 |
| `packages` | 236 |
| `plans` | 192 |
| `apps` | 92 |
| `tests` | 91 |
| `site` | 49 |
| `docs` | 46 |
| `queue` | 27 |
| `temp` | 12 |
| `.github` | 10 |
| `.agents` | 9 |
| `scripts` | 6 |
| `ci` | 5 |
| `output` | 5 |
| `dna` | 2 |
| `.gitignore` | 1 |
| `CONTRIBUTING.md` | 1 |
| `DEPLOYMENT_SUMMARY.md` | 1 |

## Deletions and dashboard files

The four staged deletions under `apps/nhipdieuxanh-orchestrator/` are still present on disk, but remain staged as deletions. They belong to the retired Nhịp Điệu Xanh target and are not re-added. Current Git deletions that are absent on disk are listed separately in the CSV. No dashboard source file is currently marked deleted in Git while still present on disk; the dashboard source changes are already represented as modified or untracked paths.

## Release disposition

The worktree remains a mixed, unreviewed candidate; no files were staged by inventory generation. See [`go-live-bug-ledger.md`](go-live-bug-ledger.md) for tracker and issue triage.
