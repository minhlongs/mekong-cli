# Phase 04: Dispatcher Integration (RAG)

## Overview
- **Priority:** Critical
- **Status:** Not Started
- **Description:** Integrate semantic search into the mission dispatching flow to enable Deep Knowledge Injection (L9).

## Implementation Steps
1. Update `lib/mission-dispatcher.js`:
   - Import `vector-service.js`.
   - Before building the mission prompt, embed the task/goal.
   - Search `knowledge` table for top 5 relevant chunks.
   - Search `history` table for top 3 similar past missions (successful ones).
2. Format the retrieved context into a `KNOWLEDGE INTEL` section in the prompt.
3. Add a `RELEVANT HISTORY` section to prevent repeating past mistakes.
4. Verify by inspecting generated mission files in `tasks/processed/`.

## Todo List
- [ ] Integrate vector search in mission-dispatcher.js
- [ ] Update prompt building logic
- [ ] Add Knowledge Intel section
- [ ] Add Relevant History section
- [ ] End-to-end verification
