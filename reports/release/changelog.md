# Changelog — algo-trader

## [Unreleased] — 2026-03-22

### Added
- **Compliance Rules Engine** — Regulatory compliance validation system
  - `SANCTIONS_001`: Sanctions Screening (OFAC/UN/EU lists)
  - `POSITION_001`: Position Limit Check ($1M default)
  - `JURISDICTION_001`: Jurisdiction Validation (KP/IR/SY/CU blocked)
  - `VOLUME_001`: Daily Volume Limit ($100K single trade)
- New module: `src/arbitrage/compliance/`
  - `compliance-types.ts` — Type definitions
  - `compliance-rules.ts` — Built-in rules engine

### Changed
- Removed hardcoded license secret — now requires env var

### Fixed
- Added `ExecutionEngine` type to resolve TS2305 error
- Resolved 123 TypeScript errors across 29 files
- Fixed redis-rate-limiter mock — 334/334 suites pass

---

## [v1.0.0] — 2026-03-20

### Released
- Initial production release
- Full RaaS Gateway integration
- Sophia AI Factory scaffold
- ROI Calculator, CRM, case studies
- Security: removed private app projects from public repo

---

**Total Changes:** 9 commits since last release
**Test Coverage:** 270 tests across 25 files (100% pass)
