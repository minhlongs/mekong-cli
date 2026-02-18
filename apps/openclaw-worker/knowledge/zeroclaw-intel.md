# 🦀 ZeroClaw Intel — 因糧於敵 (Dùng lương địch)

> Assessed: 2026-02-18 | Status: NOTED (P3) | Action: Learn, Don't Adopt

## Source
- Repo: https://github.com/theonlyhennygod/zeroclaw (zeroclaw-labs/zeroclaw)
- Stack: 100% Rust, single binary ~3.4MB, <5MB RAM
- License: AGPL-3.0
- Community: 61 contributors (Harvard/MIT/Sundai.Club)

## DNA Worth Extracting (因糧於敵)

### 1. Memory System (⭐⭐⭐)
- Full-stack search: SQLite + vector + embedding + keyword
- Zero external deps (no Pinecone, no ElasticSearch)
- Config: `backend = "sqlite"`, `embedding_provider = "openai"`, `vector_weight = 0.7`
- Tôm Hùm gap: Chỉ dùng flat files (`wins.jsonl`, `knowledge/*.md`)
- **Tiêm khi:** Evolution Engine Level 7+

### 2. Trait Architecture (⭐⭐⭐)
- Provider/Channel/Tool/Memory all swappable via config, zero code change
- Tôm Hùm gap: `anthropic-adapter.js` hardcoded routing
- **Tiêm khi:** Major refactor cycle

### 3. Security Model (⭐⭐)
- Deny-by-default channel allowlists
- Workspace scoping per agent
- Pairing + strict sandboxing

## Tại sao KHÔNG adopt
- 有所不取: Rust rewrite = 3-6 tháng, phá vỡ momentum
- Tôm Hùm orchestration (CTO/11 daemons/evolution) >> ZeroClaw (single agent)
- Node.js ecosystem (ClaudeKit, tmux, nohup) đã mature
- M1 16GB chạy Node.js vẫn đủ cho 4 workers

## Kết luận
> 上兵伐謀 — Học thiết kế, không copy code. Memory system pattern sẽ tự nhiên tiêm qua Brain Surgery khi đủ trưởng thành.
