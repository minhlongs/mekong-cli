# Phase 05: Wave 197 Variance Gamma Process Option Pricing

## Target Directory: `/Users/macbook/algo-trader/src/desk/variancegamma/`
- Files strictly < 180 LOC:
  1. `variance-gamma-moments-types.ts`
  2. `variance-gamma-moments-math.ts`
  3. `variance-gamma-moments-engine.ts`
  4. `index.ts`
- Tests strictly < 180 LOC:
  - `tests/unit/desk/variancegamma/variance-gamma-moments.test.ts`

## Success Criteria
- Subordinated Brownian motion characteristic function with drift compensator omega.
- Analytical moments (variance, skewness, excess kurtosis).
- Adaptive Gil-Pelaez quadrature option pricing.
- 0 `:any`, 100% test pass.
