# Monorepo TypeScript & Lint Audit Analysis

## 1. Executive Summary

An audit of the `mekong-cli` monorepo has been performed to resolve typechecking, linting, and dependency resolution issues. The audit revealed three core systemic issues:

1. **Nested Workspace Mismatch (Cleo-New)**: The root `tsconfig.json` includes `packages/**/*` in its compilation scope. However, `packages/cleo-new` is a nested, separate `pnpm` monorepo that is explicitly excluded from the root `pnpm-workspace.yaml`. Compiling it under the root TypeScript context causes thousands of type errors (~4,200 out of 4,500 errors) due to library mismatches (e.g. `ES2025` library features like `findLast` being flagged as unsupported) and unresolved workspace dependencies (like `@cleocode/caamp`, `@cleocode/lafs`, `@cleocode/cant`).
2. **Missing React Types in Global Scope**: The root `tsconfig.json` explicitly lists `"types": ["vitest/globals", "node", "@cloudflare/workers-types"]`. This overrides TypeScript's default behavior and prevents types from other installed packages (such as `@types/react` and `@types/react-dom`) from being loaded globally. Consequently, compiling React files in `@mekong/ui` (under `packages/ui`) fails with errors stating `JSX element implicitly has type 'any' because no interface 'JSX.IntrinsicElements' exists`.
3. **Casing Mismatches in UI Exports**: The files in `packages/ui/src/components` are named in kebab-case (e.g., `tenant-card.tsx`, `gateway-status.tsx`, `forecast-chart.tsx`), but their corresponding `index.ts` files export them using camelCase import paths (e.g., `./tenantCard`, `./gatewayStatus`, `./forecastChart`), leading to `TS2307: Cannot find module` errors.
4. **Interactive ESLint Prompt in next lint**: Running the lint suite (`npx turbo run lint`) fails on the `mekong-ide` app because Next.js's `next lint` command prompts the console for configuration selection when no `.eslintrc` or `eslint.config` is present, causing non-interactive lint tasks to hang and fail.

---

## 2. TypeScript Compile Errors (Root Audit)

Running `npx tsc --noEmit` from the root produces approximately 4,526 lines of error logs. The breakdown of these errors is as follows:

### A. Nested Workspace Mismatches (`packages/cleo-new/packages/**/*`)
* **Errors**: ~4,200 lines
* **Typical Errors**:
  * `error TS2550: Property 'findLast' does not exist on type 'IvtrPhaseEntry[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.` (e.g. `packages/cleo-new/packages/core/src/lifecycle/ivtr-loop.ts:251`)
  * `error TS2307: Cannot find module '@cleocode/caamp' or its corresponding type declarations.`
  * `error TS2339: Property 'data' does not exist on type 'EngineResult'. Property 'data' does not exist on type 'EngineFailure'.`
* **Root Cause**: The nested workspace `cleo-new` utilizes strict NodeNext resolution and target libraries targeting ES2025. When the root `tsconfig.json` attempts to compile these files under `packages/**/*` using ES2022 target and no nested workspace references mapping, it fails to find its dependencies and language features.

### B. Missing JSX/React Type Declarations (`packages/ui/src/**/*`)
* **Errors**: ~250 lines
* **Typical Errors**:
  * `packages/ui/src/components/trading/price-display.tsx(3,24): error TS7016: Could not find a declaration file for module 'react'.`
  * `packages/ui/src/components/trading/price-display.tsx(29,7): error TS2875: This JSX tag requires the module path 'react/jsx-runtime' to exist, but none could be found.`
  * `packages/ui/src/components/pr/sentiment-bar.tsx(8,5): error TS7026: JSX element implicitly has type 'any' because no interface 'JSX.IntrinsicElements' exists.`
* **Root Cause**: The root `tsconfig.json` restricts global types using `"types": ["vitest/globals", "node", "@cloudflare/workers-types"]` but does not include `"react"` or `"react-dom"`, preventing JSX element resolution for the UI components.

### C. File Casing Mismatch in UI Component Exports
* **Errors**: 25 lines
* **Typical Errors**:
  * `packages/ui/src/components/raas/index.ts(1,28): error TS2307: Cannot find module './tenantCard' or its corresponding type declarations.`
  * `packages/ui/src/components/sales/index.ts(1,26): error TS2307: Cannot find module './dealCard' or its corresponding type declarations.`
  * `packages/ui/src/components/security/index.ts(1,26): error TS2307: Cannot find module './vulnCard' or its corresponding type declarations.`
* **Root Cause**: The folders inside `packages/ui/src/components/` use kebab-case file naming convention, but their corresponding `index.ts` export modules use camelCase filenames in imports (e.g. importing `./tenantCard` when the file is `./tenant-card.tsx`).

---

## 3. Dependency & Node Modules Resolution Audit

### A. Workspace Dependency `@cleocode/caamp`
* `@cleocode/caamp` is correctly set up as a packages workspace under `packages/cleo-new/packages/caamp`.
* It is referenced inside `packages/cleo-new/packages/adapters/package.json` as `"@cleocode/caamp": "workspace:*"`.
* Resolution fails during top-level root compile because `pnpm` in the root workspace does not see it since `packages/cleo-new` is excluded from the root `pnpm-workspace.yaml`.
* Running typecheck independently inside `packages/cleo-new` with `pnpm --filter @cleocode/monorepo typecheck` correctly resolves it using its own pnpm workspace links.

### B. `@cloudflare/workers-types`
* The package `@cloudflare/workers-types` is present in root `package.json` (`devDependencies`: `"^4.20260528.1"`).
* The root `tsconfig.json` correctly includes it in `"types"`.
* No resolution issues were detected for wrangler/workers packages that are part of the root workspace (like `packages/mekong-engine`).

---

## 4. ESLint Check Details

### A. Turbo Lint Failure
* Running `npx turbo run lint --concurrency=1` fails on the task `mekong-ide#lint`.
* Command: `next lint`
* Execution Log: The task hangs/aborts because Next.js interactive CLI attempts to ask the developer for ESLint configuration choices.
* Root Cause: No ESLint config file (`.eslintrc.json` or `eslint.config.js`) exists in `apps/mekong-ide`.

---

## 5. Remediation Plan

To resolve these build, typescript compilation, and linting issues, we propose the following concrete changes:

### Step 1: Update Root `tsconfig.json` to Exclude nested `cleo-new`
Add `packages/cleo-new` and `packages/cleo-new/**/*` to the `exclude` block of the root `tsconfig.json`. This will isolate the top-level compilation and prevent the root compile from running into library mismatches.

```json
  "exclude": [
    "**/node_modules",
    "**/.next",
    "**/dist",
    "**/build",
    "apps/**/*",
    "src/**/*",
    "packages/cleo-new/**/*"
  ]
```

### Step 2: Add React types to root `tsconfig.json` `"types"` configuration
Ensure React types are included in the compiler types resolution array:
```json
  "types": ["vitest/globals", "node", "@cloudflare/workers-types", "react", "react-dom"]
```

### Step 3: Correct File Imports in `packages/ui/src/components`
Fix the import paths in the `index.ts` files of the UI components to match their actual kebab-case file names on disk.

1. **`packages/ui/src/components/raas/index.ts`**:
   * Change `./tenantCard` to `./tenant-card`
   * Change `./gatewayStatus` to `./gateway-status`
   * Change `./mcuGauge` to `./mcu-gauge`
   * Change `./sdkPreview` to `./sdk-preview`
2. **`packages/ui/src/components/sales/index.ts`**:
   * Change `./dealCard` to `./deal-card`
   * Change `./pipelineStage` to `./pipeline-stage`
   * Change `./forecastChart` to `./forecast-chart`
3. **`packages/ui/src/components/security/index.ts`**:
   * Change `./vulnCard` to `./vuln-card`
   * Change `./complianceGauge` to `./compliance-gauge`
   * Change `./threatFeed` to `./threat-feed`
   * Change `./accessMatrix` to `./access-matrix`
   * Change `./policyStatus` to `./policy-status`
   * Change `./incidentTimeline` to `./incident-timeline`

### Step 4: Add ESLint config for `apps/mekong-ide`
Create `apps/mekong-ide/.eslintrc.json` to configure ESLint for the Next.js app and prevent the interactive prompt:
```json
{
  "extends": "next/core-web-vitals"
}
```

### Step 5: Implement Independent Typecheck script for nested Monorepo
Add a script in root `package.json` to type-check `cleo-new` independently:
```json
"type-check:cleo": "pnpm --filter @cleocode/monorepo typecheck"
```
And adjust `type-check` script in root `package.json` to run both:
```json
"type-check": "tsc --noEmit && pnpm --filter @cleocode/monorepo typecheck"
```
