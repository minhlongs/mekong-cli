# Natural Language Auto-Harness: mk auto command

**Ngày:** 260811 · **Priority:** MEDIUM · **Status:** DONE — all phases implemented & verified

- [x] **Phase 01** — 01.01 — `src/mk7/core/router.py` — intent classifier (haiku→openrouter→strategist fallback, JSON-strict, HITL <0.7)
- [x] **Phase 02** — 01.02 — `src/mk7/core/graph.py` — DAG state machine (checkpoint/resume, retry ≤3, budget 20 nodes/60 calls, validate cycle)
- [x] **Phase 03** — 01.03 — `src/mk7/core/gates.py` — gate registry (5 default + 3 hard, exit 42, whitelist)
- [x] **Phase 04** — 01.04 — `src/mk7/commands/auto.py` — router→graph→gate, --resume/--decision, exit 0/1/42
- [x] **Phase 05** — 01.05 — `src/mk7/core/dispatch.py` + `src/mk7/core/tools.py` — node dispatch 1M, tool whitelist (read/write/cat/bash-test)
- [x] **Phase 06** — 01.06 — tests: 45 passed (router 10, graph 14, gates+tools 12, tools 6, +3) coverage router 93% / graph 95%
- [x] **Phase 07** — 01.07 — `HARNESS.md` — Appendix A: mk auto usage, gates, resume/decision, whitelist, danger levels, exit codes
- [x] **Phase 08** — 01.08 — Verified live:
  - success: "tạo file hello.txt" → exit 0, 3 nodes, file thật = "hello"
  - gate deploy: exit 42, chặn đúng
  - resume+approve: exit 0, 7 nodes hoàn tất (fix: reset blocked→pending)
  - deny: exit 42
  - chi-tien: gate=spend_money đúng
  - rm/xoa-file: danger=high, gate=delete_data, exit 42, file không bị xóa
- [x] **Phase 09** — 01.09 — Review: bugs fixed (parser trailing prose, parent-dir write, blocked-node resume, router HitlGate fallback)
