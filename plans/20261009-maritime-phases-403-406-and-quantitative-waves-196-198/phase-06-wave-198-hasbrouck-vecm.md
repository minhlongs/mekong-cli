# Phase 06: Wave 198 Hasbrouck VAR/VECM Information Content

## Target Directory: `/Users/macbook/algo-trader/src/desk/hasbrouck/`
- Files strictly < 180 LOC:
  1. `hasbrouck-vecm-types.ts`
  2. `hasbrouck-vecm-math.ts`
  3. `hasbrouck-vecm-engine.ts`
  4. `index.ts`
- Tests strictly < 180 LOC:
  - `tests/unit/desk/hasbrouck/hasbrouck-vecm.test.ts`

## Success Criteria
- Bivariate structural VAR with trade signed volume.
- Impulse response function (IRF) and permanent price impact.
- Hasbrouck information share $R_w^2$ variance decomposition.
- 0 `:any`, 100% test pass.
