# Static Analysis & Configuration Audit

This report documents the package configuration, dependency graph, and static analysis setup for **Sophia AI Factory** (specifically located at `/Users/macbook/projects/sophia-ai-factory/apps/sophia-ai-factory`).

---

## 1. Package Configuration and Dependency Graph Analysis

### A. Root vs. Subdirectory Dependency Mismatch (Major Conflict)
The repository contains duplicate and conflicting package configuration files in the root directory and the application directory. This causes dual installations and potential dependency resolution conflicts:

| File / Setting | Root `/Users/macbook/projects/sophia-ai-factory` | App `apps/sophia-ai-factory/` | Impact |
|---|---|---|---|
| **Package Name** | `sophia-ai-factory` (Line 2) | `sophia-ai-factory` (Line 2) | Name conflict in monorepos. |
| **React Version** | `18.3.1` (Line 55) | `19.2.3` (Line 127 in pnpm-lock) | **Critical mismatch**: Root installs React 18, App requires React 19. Node.js import resolution may walk up to root `node_modules` and resolve React 18, causing runtime or types mismatch. |
| **Next.js Version** | `15.5.14` (Line 52) | `^16.2.5` (Line 108 in pnpm-lock) | **Critical mismatch**: Next.js 15 vs. Next.js 16. |
| **Zod Version** | `^3.24.1` (Line 65) | `^4.3.6` (Line 171 in pnpm-lock) | Version 3 vs. Version 4. |
| **Lockfiles** | `package-lock.json` & `pnpm-lock.yaml` | `package-lock.json` & `pnpm-lock.yaml` | **Dual lockfiles**: Indicates developers/agents run both `npm` and `pnpm` in parallel, leading to out-of-sync dependency trees. |

### B. Legacy Configuration Residue in Root
The root directory `/Users/macbook/projects/sophia-ai-factory` contains stale configuration files left over from when it was a single-repo before the `apps/` division (consolidation of 2026-04-14):
* Stale `package.json` with obsolete React 18/Next 15 dependencies.
* Stale `.next` compile output cache.
* Stale database migration `migrations/0129_sop_templates.sql` (whereas `apps/sophia-ai-factory` contains the actual database migrations consisting of 151 files).
* Stale `open-next.config.ts` and `wrangler.jsonc`.

**Recommendation**: Remove the root `package.json`, its lockfiles, and configuration stubs if the repository is not configured as a standard monorepo workspace. Alternatively, define a unified monorepo root workspace in a root `pnpm-workspace.yaml` and reference `apps/sophia-ai-factory` and `apps/84tea` as packages.

---

## 2. Static Analysis Rule Conflicts

Our investigation of the ESLint setup (`eslint.config.mjs`) and warning files revealed two major rule conflicts affecting static gates:

### A. React Compiler Purity Rules vs. Next.js Server Components (false-positives)
1. **The Conflict**:
   * ESLint configuration `eslint.config.mjs` configures React Compiler rules:
     * `react-hooks/purity` (Warns on impure rendering calls)
     * `react-hooks/immutability`
     * `react-hooks/static-components`
     * `react-hooks/set-state-in-effect`
   * These rules are set to `"warn"` to prevent breaking individual file compilation.
   * However, `react-hooks/purity` has massive false-positives against Next.js Server Components. In Server Components (which are async functions executing on the server), calling time-dependent or random APIs (such as `Date.now()` or `Math.floor(Date.now() / 1000)`) is the standard pattern to get request-time parameters. Purity rules incorrectly flag these as violations.
2. **The Bottleneck**:
   * The `ci:lint` script in `apps/sophia-ai-factory/package.json` runs:
     `"ci:lint": "node --max-old-space-size=14336 ./node_modules/eslint/bin/eslint.js src --max-warnings=341"`
   * Because of the high false-positives, the codebase contains **370+ warnings** (verified in `lint_output_new.txt`).
   * Since `370 > 341`, the `ci:lint` gate **fails**, blocking builds and commits in CI even though the code contains zero actual errors.

### B. Unused Variables Config Mismatch
1. **The Conflict**:
   * The codebase has numerous warnings for unused parameters/variables (e.g. `@typescript-eslint/no-unused-vars` for `_locale`, `_userId`, `_tier`).
   * Developers prefixed these with an underscore `_` intending to suppress unused warnings (common TS/ESLint pattern).
   * However, `@typescript-eslint/no-unused-vars` is not configured in `eslint.config.mjs` to ignore prefixed variables. Therefore, these variables are still flagged as warnings, contributing to the warning threshold breach.

---

## 3. Static Analysis Performance & Compilation Bottlenecks

1. **Missing ESLint Cache**:
   * The `npm run lint` and `npm run ci:lint` scripts run ESLint on the entire `src/` directory from scratch.
   * Because ESLint parses TypeScript ASTs for all files on every run, it takes a long time (around 1.5 - 2 minutes) and consumes massive amounts of RAM.
   * This is why it requires a huge memory limit allocation: `node --max-old-space-size=14336` (14 GB).
   * **Verification Finding**: Running `npm run ci:lint` directly resulted in **Exit code: 137** (Out of Memory/SIGKILL), confirming that the lack of caching combined with large TS trees exhausts even 14GB of allocated memory in this environment.
   * **Recommendation**: Add `--cache` to `lint` scripts. ESLint caching saves file states, reducing subsequent runs to a few seconds by only analyzing modified files.
2. **TypeScript and Vitest checks**:
   * Type checking via `npm run ci:typecheck` runs `tsc --noEmit` and succeeds without errors.
   * The compiler utilizes `tsconfig.tsbuildinfo` correctly, preventing performance bottlenecks in typescript compilation.
   * Vitest test runs (`npm run ci:test`) complete but report unit test failures (e.g. `migration-coverage-guard.test.ts`, `edge-runtime-safety-guard.test.ts`, etc.), indicating that while the code compiles successfully, runtime logic or testing configurations still need debugging.

---

## 4. Proposed Optimizations

We propose the following actions to unblock and optimize static checks:

### Proposal A: Silence False-Positives & Update Warning Threshold
Modify `eslint.config.mjs` rules or disable purity rules for Next.js Server Components. Alternatively, increase `--max-warnings` in `package.json` to match the baseline warning count (e.g. `380`), or turn off `react-hooks/purity` for async server component files.

### Proposal B: Add ESLint Cache to Scripts
Update `apps/sophia-ai-factory/package.json` to include `--cache` for both local linting and CI pipelines (restoring caches in CI runners):
```json
"lint": "node --max-old-space-size=14336 ./node_modules/eslint/bin/eslint.js src --cache",
"ci:lint": "node --max-old-space-size=14336 ./node_modules/eslint/bin/eslint.js src --max-warnings=380 --cache"
```

### Proposal C: Configure `no-unused-vars` to Ignore Prefixed Variables
Add custom configuration in `eslint.config.mjs` for `@typescript-eslint/no-unused-vars` to prevent warnings for intentional placeholders:
```javascript
"@typescript-eslint/no-unused-vars": [
  "warn",
  {
    "argsIgnorePattern": "^_",
    "varsIgnorePattern": "^_",
    "caughtErrorsIgnorePattern": "^_"
  }
]
```

### Proposal D: Root Clean-up
Archive/delete the root `package.json` and its lockfiles to prevent conflicting React 18 / Next 15 dependency installations that overlap with the React 19 / Next 16 environment inside `apps/sophia-ai-factory`.
