# Plan C: Contain the cleo-new Rust/Python boundary

## Context
packages/cleo-new has very high fan-in and is a single sink that touches parser, core, raas, api, commands, and daemon.
The boundary between Rust and Python is currently hard to reason about.
Hotspot functions show the boundary carries parsing, migration, and push traffic at the highest volume in the repo.

## Observations
- cleo-new/cant-core is used like a shared runtime service.
- Many layers call into cleo-new directly, which creates tight coupling.
- Parsing and push functions are natural bottlenecks; a latency spike in Rust FFI risks widespread downstream failures.

## Proposal: Interface contract and graduation path
1. Define one canonical interface contract for cleo-new usage in Python.
- Accept only typed payloads from canonical modules, not from CLI or daemon directly.
2. Introduce a boundary service around cleo-new calls.
- Python should call cleo-new through a facade, not directly from every caller.
3. Cap new direct usage without a design review.
- Any new caller of cleo-new must include request/response schema and fallback behavior.

## Steps
- Inventory direct cleo-new call sites.
- Add one facade module for current usage patterns.
- Add typed request/response objects near the Rust boundary.
- Document failure modes and expected recovery behavior.

## Acceptance Criteria
- All direct calls to cleo-new are routed through the boundary module in follow-on work.
- No observable increase in latency from the extra indirection.
> Created: 2026-07-12
