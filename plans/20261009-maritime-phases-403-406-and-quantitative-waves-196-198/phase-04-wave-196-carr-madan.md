# Phase 04: Wave 196 Carr-Madan Static Replication

## Target Directory: `/Users/macbook/algo-trader/src/desk/carrmadan/`
- Files strictly < 180 LOC:
  1. `carr-madan-static-types.ts`
  2. `carr-madan-static-math.ts`
  3. `carr-madan-static-engine.ts`
  4. `index.ts`
- Tests strictly < 180 LOC:
  - `tests/unit/desk/carrmadan/carr-madan-static.test.ts`

## Success Criteria
- Static spanning identity calculation with discrete strike regularization.
- Reflection boundary parity for barrier option replication.
- 0 `:any`, 100% test pass.
