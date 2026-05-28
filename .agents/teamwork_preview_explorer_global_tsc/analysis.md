# TypeScript Typechecking and ESLint Error Analysis

This report documents all remaining TypeScript compilation and ESLint errors across the `mekong-cli` monorepo, identifies their root causes, and proposes concrete remediation strategies.

---

## 1. Global TypeScript Compilation Errors

Running `npx tsc --noEmit` at the repository root produces errors due to:
- Missing workspace project path mappings in the root `tsconfig.json`.
- Missing or misconfigured path mappings inside individual package TS configs.
- Missing stub implementations/declarations for gitignored private packages.
- Minor syntax and type cast bugs in packages and test files.

### Detailed Compilation Errors & Remediations

#### Issue 1.1: Missing Root Path Mappings for Workspace Packages
- **Files Affected**: Root `tsconfig.json`
- **Error Types**: `TS2307: Cannot find module '@mekong/raas-sdk'`
- **Description**: The root `tsconfig.json` includes `packages/**/*` in type-checking but lacks path mapping configuration for workspace packages like `@mekong/raas-sdk`, leading to compilation failures when `tsc` is run at the root.
- **Proposed Solution**: Add the workspace packages path mappings to the root `tsconfig.json` under `compilerOptions.paths`.
  
  ```json
  "paths": {
    "classVarianceAuthority": ["node_modules/class-variance-authority"],
    "@mekong/raas-sdk": ["packages/raas-sdk/src/index.ts"],
    "@openclaw/rd-engine/*": ["packages/rd-engine/dist/*"],
    "@openclaw/raas-marketplace": ["packages/raas-marketplace/dist/index.d.ts"]
  }
  ```

---

#### Issue 1.2: Path Mapping Casing and Sub-path Imports for `@openclaw/raas-marketplace`
- **Files Affected**: 
  - `packages/mekong-cli-core/tsconfig.json`
  - `packages/mekong-cli-core/src/cli/commands/raas-marketplace.ts`
- **Error Messages**:
  - `raas-marketplace.ts:7:32 - error TS2307: Cannot find module '@openclaw/raas-marketplace/catalog'`
  - `raas-marketplace.ts:8:40 - error TS2307: Cannot find module '@openclaw/raas-marketplace/storefront'`
  - `raas-marketplace.ts:9:26 - error TS2307: Cannot find module '@openclaw/raas-marketplace/sales-bot'`
  - `raas-marketplace.ts:10:32 - error TS2307: Cannot find module '@openclaw/raas-marketplace/analytics'`
- **Description**: 
  1. The path mapping in `mekong-cli-core/tsconfig.json` maps `@mekong/raas-marketplace/*` with a `@mekong/` prefix instead of `@openclaw/`.
  2. The code imports from sub-paths like `@openclaw/raas-marketplace/catalog` but the compiled module only bundles all declarations inside `dist/index.d.ts` without exporting separate sub-path files.
- **Proposed Solution**: 
  1. Update imports in `raas-marketplace.ts` to load directly from the root package:
     ```typescript
     // Before
     import { ProductCatalog } from '@openclaw/raas-marketplace/catalog';
     
     // After
     import { ProductCatalog, generateStorefrontJSON, SalesBot, SalesAnalytics } from '@openclaw/raas-marketplace';
     ```
  2. Add root-level path mapping to `packages/mekong-cli-core/tsconfig.json`:
     ```json
     "@openclaw/raas-marketplace": ["../raas-marketplace/dist/index.d.ts"]
     ```

---

#### Issue 1.3: Misconfigured Path Mapping for `@openclaw/rd-engine`
- **Files Affected**: `packages/mekong-cli-core/tsconfig.json`
- **Error Messages**:
  - `rd.ts:19:53 - error TS2307: Cannot find module '@openclaw/rd-engine/sources/github-trending'`
- **Description**: The path mapping in `mekong-cli-core/tsconfig.json` points to `../rd-engine/src/*`. However, `packages/rd-engine` is gitignored and does not have a `src/` folder locally; only compiled output exists in `dist/`.
- **Proposed Solution**: Update `tsconfig.json` path mapping to point to the `dist` folder:
  ```json
  // Before
  "@openclaw/rd-engine/*": ["../rd-engine/src/*"]

  // After
  "@openclaw/rd-engine/*": ["../rd-engine/dist/*"]
  ```

---

#### Issue 1.4: Missing Stubs for Gitignored Private Packages
- **Packages**: `@openclaw/agi-evolution` and `@openclaw/vc-governance`
- **Files Affected**: `packages/mekong-cli-core/src/cli/commands/agi.ts`, `vc-governance.ts`
- **Error Messages**:
  - `agi.ts:8:80 - error TS2307: Cannot find module '@openclaw/agi-evolution/self-improver'`
  - `vc-governance.ts:8:32 - error TS2307: Cannot find module '@openclaw/vc-governance/pitch-generator'`
- **Description**: Both packages are gitignored stubs that only contain `package.json`. No source files or types exist, causing typecheck failure.
- **Proposed Solution**: Propose creating a unified stubs file at `packages/mekong-cli-core/src/types/openclaw-stubs.d.ts` to define these modules:
  ```typescript
  declare module '@openclaw/agi-evolution/self-improver' {
    export function analyzeCodebase(): any;
    export function getQualityScore(): number;
    export function generateRefactoringProposals(): any;
  }
  declare module '@openclaw/agi-evolution/version-tracker' {
    export function checkVersions(): any;
  }
  declare module '@openclaw/agi-evolution/benchmark' {
    export class BenchmarkRunner {
      run(): any;
    }
  }
  declare module '@openclaw/vc-governance/pitch-generator' {
    export class PitchGenerator {
      generatePitchData(kpis: any): any;
      generateOneLiner(): string;
    }
  }
  declare module '@openclaw/vc-governance/data-room' {
    export class DataRoom {
      listDocuments(): any[];
    }
  }
  declare module '@openclaw/vc-governance/iso-compliance' {
    export class ComplianceEngine {
      auditISO27001(): any;
      auditSOC2(): any;
      checkGDPR(): any[];
      generateComplianceReport(): string;
    }
  }
  declare module '@openclaw/vc-governance/exit-engine' {
    export class ExitEngine {
      calculateValuation(method: string, inputs: any): number;
      recommendStrategy(inputs: any): any;
    }
  }
  ```

---

#### Issue 1.5: Implicit 'any' Types and Type Cast Errors
- **Files Affected**:
  - `packages/mekong-cli-core/src/cli/commands/rd.ts` (lines 38-40, 73-74)
  - `packages/mekong-cli-core/src/cli/commands/vc-governance.ts` (line 69)
  - `packages/openclaw-engine/src/raas/raas-server.ts` (line 53)
  - `packages/zalo-parser/tests/index.test.ts` (lines 108, 145-151)
  - `packages/mekong-engine/test/observability-alerts.test.ts` (lines 156-182)
- **Proposed Solutions**:
  1. Add type annotations to callbacks in `rd.ts` and `vc-governance.ts` (e.g. `(r: any)`, `(c: any)`).
  2. In `raas-server.ts`, double cast body to resolve TS2352: `body as unknown as OnboardingRequest`.
  3. In `zalo-parser/tests/index.test.ts`, cast fetch JSON responses: `const json = await res.json() as any;`.
  4. In `observability-alerts.test.ts`, cast return value: `const message = formatSlackMessage(alert) as any;`.

---

#### Issue 1.6: Systematic Typo and Import Casing in `packages/ui`
- **Files Affected**: 20+ components in `packages/ui` (e.g., `badge.tsx`, `button.tsx`, `card.tsx`) and all folder `index.ts` files.
- **Error Messages**:
  - `TS2307: Cannot find module 'classVarianceAuthority'`
  - `TS2307: Cannot find module './riskHeatmap' or './controlCard'` (Casing Mismatch)
- **Description**:
  1. Components import `"classVarianceAuthority"` but the actual package name is `"class-variance-authority"`.
  2. Index files import using camelCase paths (e.g. `./riskHeatmap`) but the files are named with kebab-case (e.g. `risk-heatmap.tsx`).
- **Proposed Solutions**:
  1. Replace all imports of `classVarianceAuthority` with `class-variance-authority`.
  2. Update all folder `index.ts` files inside `packages/ui/src/components/` to use kebab-case file paths matching the filesystem.

---

#### Issue 1.7: Interface Extensions with Property Conflicts in `packages/ui`
- **Files Affected**:
  - `packages/ui/src/components/dashboard/command-palette.tsx` (redefines `onSelect`)
  - `packages/ui/src/components/marketing/pricing-table.tsx` (redefines `onSelect`)
  - `packages/ui/src/components/ml/eval-suite.tsx` (redefines `results`)
- **Proposed Solution**: Use `Omit` when extending `React.HTMLAttributes<HTMLDivElement>` to prevent typescript conflicts:
  ```typescript
  export interface CommandPaletteProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> { ... }
  export interface PricingTableProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'onSelect'> { ... }
  export interface EvalSuiteProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'results'> { ... }
  ```

---

#### Issue 1.8: Missing Stub Integrations for `apps/algo-trader-remote`
- **Files Affected**: `apps/algo-trader-remote/tsconfig.json`
- **Error Messages**:
  - `TS2307: Cannot find module '@agencyos/trading-core/exchanges' or '@agencyos/vibe-arbitrage-engine/strategies'`
- **Description**: The app imports submodules from placeholder workspace packages that only contain a single root `index.d.ts`.
- **Proposed Solution**: Update `apps/algo-trader-remote/tsconfig.json` paths mapping to route all sub-path queries under `@agencyos/trading-core/*` and `@agencyos/vibe-arbitrage-engine/*` to their index declaration files:
  ```json
  "paths": {
    "@agencyos/trading-core": ["../../packages/trading-core/index.d.ts"],
    "@agencyos/trading-core/*": ["../../packages/trading-core/index.d.ts"],
    "@agencyos/vibe-arbitrage-engine": ["../../packages/vibe-arbitrage-engine/index.d.ts"],
    "@agencyos/vibe-arbitrage-engine/*": ["../../packages/vibe-arbitrage-engine/index.d.ts"]
  }
  ```

---

## 2. ESLint Configuration & Dependency Errors

Running `pnpm run lint` fails due to:
1. Missing `eslint.config.js` or configuration parameters in Next.js apps (`apps/ide-ui`).
2. Missing local devDependencies (e.g. `@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`) inside packages that define their own `eslint.config.js` (`packages/i18n`).

### Detailed ESLint Remediation Strategy

1. **Install ESLint Packages locally for `@mekong/i18n`**:
   Add `@eslint/js`, `typescript-eslint`, and `eslint-plugin-react-hooks` to `@mekong/i18n` devDependencies.
2. **Add Next.js lint configurations**:
   Initialize standard Next.js ESLint configuration inside `apps/ide-ui` by creating an `.eslintrc.json`:
   ```json
   {
     "extends": "next/core-web-vitals"
   }
   ```
