# Release Manager Report — Mekong CLI
*Role: Release Manager | Date: 2026-03-11*

---

## Current Release State

- **Version:** v0.2.0 (per `src/main.py`)
- **Distribution:** PyPI (`pip install mekong-cli`)
- **License:** MIT
- **Changelog:** Not yet published (gap)
- **GitHub releases:** Status unknown — need tags to verify

---

## Versioning Strategy

Mekong CLI must follow strict **Semantic Versioning (semver 2.0)**:

```
MAJOR.MINOR.PATCH
  │      │     └── Bug fixes, prompt tuning, doc updates
  │      └──────── New commands, new agents, new LLM providers
  └─────────────── Breaking CLI interface changes, PEV API changes
```

**Current state:** v0.2.0 implies pre-stable. Path to v1.0.0:
- All 289 commands validated and tested
- PEV engine API stable (no breaking changes for 2 sprints)
- `mekong cook` success rate >90% on standard tasks
- Public CHANGELOG.md published

---

## Release Cadence

| Type | Frequency | Trigger |
|------|-----------|---------|
| Patch (0.x.Y) | As needed | Bug fix merged to main |
| Minor (0.X.0) | Bi-weekly | New command/agent batch |
| Major (X.0.0) | Quarterly | Breaking API change |
| Hotfix | Immediate | P0 production issue |

**Rule:** Never release on Fridays. Deploy window: Tuesday–Thursday only.

---

## Release Checklist

### Pre-Release (24 hours before)
- [ ] `python3 -m pytest tests/` passes (all 62 tests green)
- [ ] `npx tsc --noEmit` passes (0 TS errors)
- [ ] `grep -r "TODO\|FIXME" src/ | wc -l` = 0
- [ ] Version bumped in `src/main.py` and `pyproject.toml`
- [ ] `CHANGELOG.md` updated with all changes since last release
- [ ] `docs/` updated if architecture changed

### Release Day
- [ ] Create GitHub release with tag `vX.Y.Z`
- [ ] Auto-publish to PyPI via GitHub Actions (on tag push)
- [ ] CF Workers auto-deploy via Wrangler on tag
- [ ] Smoke test: `pip install mekong-cli==X.Y.Z && mekong version`
- [ ] Post release notes to Discord + Twitter

### Post-Release (24 hours after)
- [ ] Monitor Sentry for new error spikes
- [ ] Check PyPI download count baseline
- [ ] Verify CF Worker error rate < 0.1%

---

## Changelog Format (Keep a Changelog style)

```markdown
## [0.3.0] - 2026-04-01

### Added
- `mekong init --wizard` for guided LLM setup
- OCOP agricultural export commands (10 new commands)
- Cloudflare R2 storage adapter

### Changed
- Tôm Hùm daemon now uses CF Queues for job dispatch

### Fixed
- CF D1 migration tooling integrated into deploy pipeline
- `test_file_stats` no longer scans entire repo

### Deprecated
- `mekong ui` command — replaced by dashboard at agencyos.network
```

---

## PyPI Release Automation

Recommended GitHub Actions workflow on tag push:

```yaml
# .github/workflows/publish.yml
on:
  push:
    tags: ['v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 -m pytest tests/
      - run: python3 -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

**Status:** Not confirmed in current `.github/workflows/`. Create immediately.

---

## Recent Release History (from git log)

| Commit | Feature | Type |
|--------|---------|------|
| `f34d70f` | Anthropic SDK core engine injection | Minor |
| `83f548` | OCOP agricultural export commands | Minor |
| `d8795da` | Sophia proposal → CF Pages | Minor |
| `a1fc36` | CF Workers + D1 + KV + Queues + R2 migration | Minor |
| `41aef04` | Fix cc-cli workflow import names | Patch |

**Observation:** 5 significant commits without a version bump or GitHub release tag.
These should be batched into v0.3.0 immediately.

---

## v0.3.0 Release Candidate Contents

Based on recent commits, v0.3.0 should include:
- Cloudflare full migration (D1, KV, Queues, R2)
- Anthropic SDK core engine
- OCOP commands
- CF workflow CI fixes
- Tôm Hùm daemon improvements

**Target release date:** 2026-03-25 (2 weeks from now)

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| PyPI token exposed | Rotate immediately, use OIDC trusted publisher |
| Breaking change in minor release | Deprecation warning 1 version before removal |
| Hotfix disrupts sprint | Hotfix branch off tag, not main |
| CF Worker deploy fails | `wrangler rollback` runbook documented |

---

## Q2 Release Actions

- [ ] Create `CHANGELOG.md` and backfill from git log
- [ ] Set up PyPI trusted publisher (OIDC) in GitHub Actions
- [ ] Tag v0.3.0 and publish to PyPI
- [ ] Create GitHub Releases page with release notes
- [ ] Define v1.0.0 criteria and publish as GitHub milestone
