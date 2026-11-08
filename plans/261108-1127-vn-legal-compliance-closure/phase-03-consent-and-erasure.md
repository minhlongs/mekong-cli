# Phase 03 — Consent Log & Real Subject Erasure

- **Status:** pending
- **Violation:** L3 — DSAR requests are recorded but never honoured, and no consent log exists
- **Files touched:** `src/core/privacy_engine.py`, `src/cli/commands/privacy_command.py`, `tests/test_antigravity_privacy.py`
- **Risk:** medium — crosses module boundary into `zalo_engine`

## Context

`src/core/privacy_engine.py` (673 lines) already implements PDPD enterprise audits,
DPIA, cross-border transfers, 72-hour breach notifications, and `handle_dsar_request`
(`:559-613`). What is missing is the two things a regulator can actually verify:

1. **No consent table.** `_init_db` (`:139-210`) creates five tables; none of them
   records consent collection or withdrawal.
2. **No real erasure.** `handle_dsar_request` inserts a row into `dsar_requests` with
   `status="PROCESSING"` and returns. It never deletes subject data from any table,
   and the status never advances to `COMPLETED`.

The live personal-data store in this repo is `src/core/zalo_engine.py`, which stores
`followers(user_id, name, phone, segment, followed_at)` and `messages(user_id, ...)`.
A delete request that leaves those rows behind is theatre.

## Requirements

1. Consent can be recorded and withdrawn, with timestamps and channel preserved.
2. `erase_subject_data(subject_id)` removes rows matching that subject from the live
   stores (`zalo_engine.followers` by `user_id` or `phone`, `zalo_engine.messages` by
   `user_id`, and `dsar_requests` other than the active request) and returns a
   per-store count.
3. A `RIGHT_TO_DELETE` DSAR executes the purge and flips its own status to `COMPLETED`.
4. The CLI exposes `mekong privacy consent` and `mekong privacy erase` in Vietnamese.

## Steps

1. In `src/core/privacy_engine.py`:
   - Add `consent_log` to `_init_db` (`consent_id`, `subject_id`, `purpose`,
     `legal_basis`, `granted`, `channel`, `created_at`, `withdrawn_at`).
   - Implement `record_consent(subject_id, purpose, legal_basis="CONSENT", channel="zalo_oa")`.
   - Implement `withdraw_consent(subject_id, purpose=None)`.
   - Implement `erase_subject_data(subject_id, zalo_db_path=None)` that opens the
     Zalo SQLite file if it exists, deletes matching `followers` (by `user_id` or
     `phone`, collecting matched `user_id`s first so `messages` keyed by `user_id`
     also go when the caller supplied a phone number) and `messages`, then withdraws
     any active consent rows for that subject. Degrade cleanly with a zero count when
     the Zalo database has not been created yet.
   - Update `handle_dsar_request` so `RIGHT_TO_DELETE` calls `erase_subject_data`,
     attaches the deletion summary to the returned dict, and writes `status="COMPLETED"`.
     `RIGHT_TO_WITHDRAW_CONSENT` calls `withdraw_consent` and likewise completes.
2. In `src/cli/commands/privacy_command.py`, add `consent` and `erase` subcommands,
   matching the module's existing Vietnamese panel style and `--json` flag.
3. In `tests/test_antigravity_privacy.py`, add tests that:
   - record and withdraw consent, asserting `granted` flips and `withdrawn_at` is set;
   - seed a follower + message in a tmp `ZaloEngine(db_path=...)`, call
     `erase_subject_data` by phone number, and assert both tables now have 0 rows for
     that subject while unrelated followers remain;
   - submit a `RIGHT_TO_DELETE` DSAR and assert the returned status is `COMPLETED`
     with non-zero deletion counts.

## Validation

```bash
python3 -m pytest tests/test_antigravity_privacy.py -q
python3 -m src.cli.main privacy consent --help
python3 -m src.cli.main privacy erase --help
```

## Risk & Mitigation

- **`core-dna-gate` triggers when `src/cli/` changes.** Adding subcommands under an
  existing command group (`privacy`) touches `src/cli/commands/privacy_command.py`,
  which matches the gate's `^src/cli/` pattern and requires a `dna/` manifest touch.
  Update `dna/core-dna.json` in the same commit so the gate stays green, without
  adding a top-level command group.
- **Database backup rule.** Any smoke test must pass explicit `db_path` arguments in
  `tmp_path`; never let a test write to `~/.mekong/privacy.db` or `~/.mekong/zalo.db`.

## Rollback

Revert the PR. New table and columns are additive; no existing rows are mutated.
