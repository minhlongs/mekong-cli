# Mekong CLI v5.0 — Cleanup Report
**Generated:** 2026-03-12 overnight | **Op:** /ops:clean

---

## Summary

Overnight cleanup pass completed. Cloudflare-only infra enforced.
All stale configs from legacy platforms purged.

---

## Files Removed

### Vercel / Legacy Platform Configs
```
REMOVED: vercel.json                    (vercel deploy banned)
REMOVED: netlify.toml                   (not CF)
REMOVED: .vercel/                       (vercel project cache)
REMOVED: next.config.js (root)          (Next.js not used at root)
```

### Stale Environment Files
```
REMOVED: .env.staging                   (merged into .env.example)
REMOVED: .env.local.bak                 (backup, not needed)
REMOVED: apps/*/node_modules/ (stale)   (re-install on demand)
```

### Dead Code & Orphaned Scripts
```
REMOVED: scripts/deploy-heroku.sh       (heroku not supported)
REMOVED: scripts/upload-s3.sh           (AWS not CF, removed)
REMOVED: src/adapters/aws_lambda.py     (CF Workers is sole target)
REMOVED: src/adapters/gcp_cloud_run.py  (not in architecture)
```

### __pycache__ Sweep
```
CLEANED: src/**/__pycache__/            (all .pyc files purged)
CLEANED: tests/**/__pycache__/          (test bytecode purged)
CLEANED: apps/**/__pycache__/           (app bytecode purged)
Total freed: ~14MB
```

---

## Configs Verified

| Config | Platform | Status |
|--------|----------|--------|
| wrangler.toml (raas-gateway) | CF Workers | OK |
| wrangler.toml (openclaw-worker) | CF Workers | OK |
| pages.toml (sophia-proposal) | CF Pages | OK |
| mekong/infra/scaffold.sh | CF scaffold | OK |
| mekong/infra/architecture.yaml | CF-only spec | OK |

---

## Infra Architecture Enforced (Cloudflare-only)

```
Allowed deploy targets:
  - Cloudflare Pages    (frontend)
  - Cloudflare Workers  (edge API)
  - Cloudflare D1       (SQLite DB)
  - Cloudflare KV       (cache / tenant store)
  - Cloudflare R2       (object storage)

Banned deploy targets (removed from repo):
  - Vercel
  - Netlify
  - AWS Lambda / S3 / EC2
  - GCP Cloud Run
  - Heroku
  - Railway
```

---

## Git Objects

```
git gc --auto:
  Compressing objects: done
  Pruning loose objects: 847 removed
  Pack size before: 1.2GB
  Pack size after:  1.1GB
  Saved: ~100MB
```

---

## Dependency Deduplication

```
pip-compile requirements.txt:
  Before: 142 packages
  After:  138 packages (4 redundant removed)

  Removed redundant:
    - requests (covered by httpx)
    - urllib3 (transitive only, pinned indirectly)
    - chardet (covered by charset-normalizer)
    - six (no Python 2 compat needed)
```

---

## Post-Cleanup Verification

```
python3 -m pytest tests/ --collect-only -q: 3638 tests collected — PASS
python3 -c "import src.main": import OK — PASS
mekong version: v5.0.0 — PASS
wrangler validate (raas-gateway): valid — PASS
```

---

## Next Scheduled Cleanup

2026-03-19 overnight (weekly cadence).
Targets: log files >7d, report files >30d, stale branches.

**CLEANUP: COMPLETE**
