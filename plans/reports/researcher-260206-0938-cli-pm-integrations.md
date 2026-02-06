# Research Report: CLI Project Management Integrations (2026)

**Date:** 2026-02-06
**Status:** COMPLETE
**Context:** Research into 2026 standards for CLI-based project management, focusing on GitHub integrations, data modeling, and performance metrics.

## 1. GitHub API Integration Strategy
The 2026 standard for CLI tools moves beyond REST to exclusively using **GraphQL (API v4)** for project management, specifically for **GitHub Projects V2**.

### Integration Patterns
*   **Projects V2**: Use GraphQL to query `user.projectV2` or `organization.projectV2`. REST API is insufficient for the new "memex" table/board views.
*   **Issues & PRs**:
    *   **Read**: Batch queries via GraphQL to fetch 100+ items in a single request (reduces latency).
    *   **Write**: Use `gh` CLI wrapper for mutations (simpler auth handling) or direct GraphQL mutations for atomic updates.
*   **Actions**: Poll workflow runs via `gh run watch` patterns (as seen in `binh-phap-cicd.md`) rather than implementing full WebSocket listeners in CLI.

### Authentication
*   **OAuth Device Flow**: Best for CLI tools distributed to users.
*   **PAT (Personal Access Tokens)**: Fine-grained tokens are mandatory. Scopes: `project` (read/write), `repo`, `user`.

## 2. Task Management Data Models
Modern CLIs adopt a strict hierarchical model to map to Agile concepts while remaining file-system friendly.

### Recommended Schema (Epic-Task-Subtask)
Based on high-performance CLI architectures (e.g., CLEO):
*   **Level 0: Epic** (Strategy) - Maps to GitHub Project "Feature" views.
*   **Level 1: Task** (Execution) - Maps to GitHub Issues.
*   **Level 2: Subtask** (Atomic) - Maps to Tasklists within Issues.

### Attributes
*   **Waves/Phases**: Group tasks by execution order (Setup → Core → Polish).
*   **Verification Gates**: Boolean flags for `implemented`, `tested`, `documented` (enforced before closure).
*   **State Machine**: `pending` → `active` (focus) → `blocked` → `completed` → `verified`.

## 3. Storage: SQLite vs JSON vs JSONL
Hybrid approaches are dominant in 2026 to balance performance and "GitOps" friendliness.

| Strategy | Use Case | Pros | Cons |
| :--- | :--- | :--- | :--- |
| **JSON** | Task State | Human-readable, Git-mergeable, zero-dep | Slow at >1k records |
| **JSONL** | Logs/History | O(1) append, corruption-resistant, atomic | Hard to query complex relationships |
| **SQLite** | Cache/Search | <5ms queries, complex joins, FTS5 search | Binary file (bad for Git), requires C bindings |

**Recommendation**:
*   **Primary State**: JSON files (sharded by Epic or Phase) for Git sync.
*   **Audit/History**: JSONL for immutable logs (`todo-log.json`).
*   **Search Index**: In-memory or transient SQLite generated from JSON.

## 4. Analytics & Productivity Metrics
CLIs now integrate "Context Monitoring" and DORA metrics directly into the terminal.

### Key Metrics
*   **Context Budget**: Tracking token usage per session (critical for LLM agents).
*   **Velocity**: Tasks completed per "Session" or "Wave".
*   **Cycle Time**: Time from `status: active` to `status: verified`.
*   **Context Switching**: Count of `focus set` changes per session.

### Reporting
*   **Markdown**: Auto-generated roadmaps (Gantt charts via Mermaid.js).
*   **JSON**: Streaming output (ndjson) for piping to dashboards.

## 5. Security & Sync
*   **Local-First**: All data stored locally, synced to cloud (GitHub/TodoWrite) on demand.
*   **Secrets**: Use system keyring (macOS Keychain, libsecret) never plain text.
*   **Sync Logic**: Bidirectional sync using "Last Write Wins" (LWW) with CRDTs (Conflict-free Replicated Data Types) gaining traction for multi-agent concurrency.

## Unresolved Questions
1.  Optimal strategy for handling GitHub rate limits in high-frequency polling?
2.  Standardized JSON schema for cross-tool task interoperability?
