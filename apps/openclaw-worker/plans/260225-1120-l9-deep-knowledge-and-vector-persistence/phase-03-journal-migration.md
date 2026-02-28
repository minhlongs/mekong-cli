# Phase 03: Journal & History Migration

## Overview
- **Priority:** High
- **Status:** Not Started
- **Description:** Migrate existing JSON history to LanceDB and update the journal to support vector persistence.

## Implementation Steps
1. Create `scripts/migrate-to-vector.js`.
2. Implement migration logic:
   - Read `data/mission-history.json` and `data/mission-outcomes.json`.
   - Embed mission summaries/tasks.
   - Batch insert into LanceDB `history` table.
3. Update `lib/mission-journal.js`:
   - Import `vector-service.js`.
   - In `recordMission()`, upsert mission data into LanceDB.
   - Maintain JSON fallback for safety.
4. Verify migration by querying LanceDB for past missions.

## Todo List
- [ ] Create migration script
- [ ] Run migration to history table
- [ ] Update mission-journal.js
- [ ] Verify data consistency
