# ZenOS Staging Deployment Runbook

**Last Updated**: 2026-06-18
**Scope**: staging validation before production migration
**Default Mode**: `audit` (do not enable `enforce` until staging passes)

---

## Objectives

1. Deploy ZenOS changes to staging.
2. Run tenant → particle migration against staging data.
3. Verify backwards compatibility with legacy tenant APIs.
4. Verify Vietnam workflows still pass:
   - `ke-toan`
   - `thue-dnvn`
   - `zalo-oa`
   - `vietqr`
5. Keep constitutional enforcement in `audit` until staging is clean.

---

## Pre-Staging Checklist

- [ ] Confirm staging DB snapshot exists.
- [ ] Confirm `~/.mekong/raas/tenants.db` is backed up.
- [ ] Confirm `~/.mekong/settings.json` is backed up.
- [ ] Confirm no production secrets are used in staging.
- [ ] Confirm `CONSTITUTIONAL_MODE=audit`.
- [ ] Confirm no `enforce` mode until migration and Vietnam regression tests pass.

---

## Staging Migration

### Dry Run

```bash
python3 scripts/migrate-tenants-to-particles.py --dry-run
```

Expected:
- tenant count matches particle count
- constitutions created
- behavior graphs initialized
- treasuries initialized
- no destructive changes

### Actual Migration

```bash
python3 scripts/migrate-tenants-to-particles.py
```

Expected:
- `particles.db` created
- compatibility flag enabled in `settings.json`
- legacy tenant APIs still work

### Rollback

```bash
python3 scripts/migrate-tenants-to-particles.py --rollback
```

Expected:
- particle tables dropped
- compatibility flag removed
- original `tenants.db` preserved

---

## Constitutional Mode

Start in `audit` mode:

```bash
export CONSTITUTIONAL_MODE=audit
```

Do **not** enable `enforce` until:
- staging migration passes
- Vietnam regression tests pass
- legacy tenant compatibility is verified
- no blocking false positives remain

If enabling enforcement later:

```bash
export CONSTITUTIONAL_MODE=enforce
```

---

## Verification Suite

Run these in order:

```bash
python3 -m pytest tests/zenos/test_migrate_tenants_to_particles.py -q
python3 -m pytest tests/zenos/test_particle_lifecycle.py -q
python3 -m pytest tests/zenos/test_constitutional_review.py -q
python3 -m pytest tests/zenos/test_vietnam_feature_regression.py -q
```

Optional full ZenOS gate:

```bash
python3 -m pytest tests/zenos/ -q
```

---

## Vietnam Regression Notes

Vietnam workflows must remain functional in particle mode.

Checklist:
- [ ] invoice creation still works
- [ ] tax reporting still works
- [ ] Zalo OA integration still works
- [ ] VietQR flow still works
- [ ] pilot user journey still works

---

## Post-Staging Decision

After staging passes:

- [ ] confirm migration is safe for production
- [ ] confirm `enforce` mode is safe
- [ ] confirm no legal/compliance blockers remain
- [ ] confirm VND payout provider decision is ready
- [ ] confirm Founder Genome key rotation design is ready
- [ ] confirm Right-to-Exit export format is ready

---

## Blockers

- No real staging deployment target exists in this repo yet.
- Staging migration must be run against a copied DB, not production.
- `CONSTITUTIONAL_MODE=enforce` should remain disabled until staging is clean.
