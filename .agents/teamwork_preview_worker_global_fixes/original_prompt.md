## 2026-05-28T09:43:43Z
Context: We need to implement all remaining global TypeScript compilation and ESLint config fixes across the mekong-cli monorepo to ensure both `npx tsc --noEmit` and `npx eslint .` run with 0 errors.
Identity: teamwork_preview_worker_global_fixes
Working directory: /Users/macbook/mekong-cli/.agents/teamwork_preview_worker_global_fixes

Please perform the following implementation tasks:

1. Run `npx prisma generate` in `apps/algo-trader-remote` to generate the client and resolve DB type errors.

2. Create type stubs file `packages/mekong-cli-core/src/types/openclaw-stubs.d.ts` with module declarations for the gitignored private packages:
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

3. Update `packages/mekong-cli-core/tsconfig.json` path mappings:
   - Map `@openclaw/raas-marketplace` to `["../raas-marketplace/dist/index.d.ts"]`.
   - Update `@openclaw/rd-engine/*` mapping to `["../rd-engine/dist/*"]` (instead of `../rd-engine/src/*`).

4. Update the root `tsconfig.json` to include the following in `compilerOptions.paths`:
   ```json
   "classVarianceAuthority": ["node_modules/class-variance-authority"],
   "@mekong/raas-sdk": ["packages/raas-sdk/src/index.ts"],
   "@openclaw/rd-engine/*": ["packages/rd-engine/dist/*"],
   "@openclaw/raas-marketplace": ["packages/raas-marketplace/dist/index.d.ts"]
   ```

5. Refactor `packages/ui` components:
   - Run a systematic find-and-replace to change imports of `"classVarianceAuthority"` to `"class-variance-authority"`.
   - Audit and update all folder `index.ts` files inside `packages/ui/src/components/*` to use kebab-case file paths matching the filesystem (e.g. change `./riskHeatmap` to `./risk-heatmap`).
   - Refactor UI props with property conflicts (use `Omit` when extending `React.HTMLAttributes<HTMLDivElement>`):
     - `packages/ui/src/components/dashboard/command-palette.tsx` (omit `'onSelect'`)
     - `packages/ui/src/components/marketing/pricing-table.tsx` (omit `'onSelect'`)
     - `packages/ui/src/components/ml/eval-suite.tsx` (omit `'results'`)

6. Update `packages/mekong-cli-core/src/cli/commands/raas-marketplace.ts`:
   - Change imports to import directly from root `@openclaw/raas-marketplace` instead of sub-paths (e.g., `import { ProductCatalog, generateStorefrontJSON, SalesBot, SalesAnalytics } from '@openclaw/raas-marketplace';`).

7. Fix implicit 'any' types and type cast errors:
   - Add type annotations (like `any`) to callback parameters in `packages/mekong-cli-core/src/cli/commands/rd.ts` and `packages/mekong-cli-core/src/cli/commands/vc-governance.ts`.
   - In `packages/openclaw-engine/src/raas/raas-server.ts`, double cast `body` to `body as unknown as OnboardingRequest`.
   - In `packages/zalo-parser/tests/index.test.ts`, cast fetch JSON responses: `const json = await res.json() as any;`.
   - In `packages/mekong-engine/test/observability-alerts.test.ts`, cast return value: `const message = formatSlackMessage(alert) as any;`.

8. Update `apps/algo-trader-remote/tsconfig.json` path mappings to point to `index.d.ts` for `@agencyos/trading-core/*` and `@agencyos/vibe-arbitrage-engine/*` packages:
   ```json
   "paths": {
     "@agencyos/trading-core": ["../../packages/trading-core/index.d.ts"],
     "@agencyos/trading-core/*": ["../../packages/trading-core/index.d.ts"],
     "@agencyos/vibe-arbitrage-engine": ["../../packages/vibe-arbitrage-engine/index.d.ts"],
     "@agencyos/vibe-arbitrage-engine/*": ["../../packages/vibe-arbitrage-engine/index.d.ts"]
   }
   ```

9. ESLint Fixes:
   - Initialize `.eslintrc.json` in `apps/ide-ui` with:
     ```json
     {
       "extends": "next/core-web-vitals"
     }
     ```
   - Add missing eslint devDependencies (`@eslint/js`, `typescript-eslint`, `eslint-plugin-react-hooks`) to `packages/i18n` (use `pnpm add -D` in the appropriate directory or update its `package.json` and run `pnpm install`).

10. Validation:
    - Run `npx tsc --noEmit` from the root to verify 0 TypeScript compilation errors.
    - Run root eslint/lint check to verify 0 lint errors.

Save your handoff report to `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_global_fixes/handoff.md`.
Finally, send a message back to the orchestrator (conversation ID: c7ee87de-d103-4253-b55e-869f1f4f6ff8) with the status and path to the handoff report.
