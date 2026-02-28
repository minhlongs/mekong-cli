# Phase 01: Setup & Vector Service

## Overview
- **Priority:** High
- **Status:** Not Started
- **Description:** Initialize LanceDB and create a generic vector service for Tôm Hùm.

## Implementation Steps
1. Install dependencies: `npm install @lancedb/lancedb`.
2. Create `lib/vector-service.js`.
3. Implement `getEmbedding(text)` helper using Antigravity Proxy.
4. Implement `initTable(name, schema)` and `upsert(tableName, data)`.
5. Implement `search(tableName, vector, filter, limit)`.
6. Add unit tests for `vector-service.js`.

## Todo List
- [ ] Install @lancedb/lancedb
- [ ] Implement embedding helper
- [ ] Create vector-service.js
- [ ] Verify connectivity on M1
