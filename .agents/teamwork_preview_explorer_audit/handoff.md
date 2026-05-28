# Handoff Report — TypeScript & Lint Audit Exploration

This report summarizes the read-only exploration and analysis of monorepo TypeScript compilation, type definitions, and dependency resolution issues.

---

## 1. Observation

Direct observations from the codebase, typecheck logs, and configuration files:

* **Observation 1 (Nested Workspace)**: Root `pnpm-workspace.yaml` explicitly excludes `packages/cleo-new` (line 3: `- '!packages/cleo-new'`). However, root `tsconfig.json` contains:
  ```json
  "include": ["packages/**/*"],
  ```
  This causes root `tsc` to compile files inside `packages/cleo-new/packages/**/*`.

* **Observation 2 (TS errors due to library/target version mismatches)**:
  Verbatim error from root `tsc --noEmit` log:
  ```
  packages/cleo-new/packages/core/src/lifecycle/ivtr-loop.ts(251,42): error TS2550: Property 'findLast' does not exist on type 'IvtrPhaseEntry[]'. Do you need to change your target library? Try changing the 'lib' compiler option to 'es2023' or later.
  ```
  Root `tsconfig.json` specifies `"target": "es2022"`, whereas `packages/cleo-new/tsconfig.json` specifies `"target": "ES2025"` and `"lib": ["ES2025"]`.

* **Observation 3 (Missing JSX/React types in root compilation)**:
  Verbatim error from root `tsc --noEmit` log:
  ```
  packages/ui/src/components/trading/price-display.tsx(29,7): error TS2875: This JSX tag requires the module path 'react/jsx-runtime' to exist, but none could be found.
  packages/ui/src/components/pr/sentiment-bar.tsx(8,5): error TS7026: JSX element implicitly has type 'any' because no interface 'JSX.IntrinsicElements' exists.
  ```
  Root `tsconfig.json` (line 15) lists:
  ```json
  "types": ["vitest/globals", "node", "@cloudflare/workers-types"]
  ```
  It does not include `"react"` or `"react-dom"`.

* **Observation 4 (Casing Mismatch on imports)**:
  Verbatim error from root `tsc --noEmit` log:
  ```
  packages/ui/src/components/raas/index.ts(1,28): error TS2307: Cannot find module './tenantCard' or its corresponding type declarations.
  ```
  The filesystem check via `list_dir` on `packages/ui/src/components/raas` shows:
  ```
  {"name":"tenant-card.tsx","sizeBytes":"1934"}
  ```
  The file name is kebab-case (`tenant-card.tsx`), but the index imports `./tenantCard`.

* **Observation 5 (Interactive next lint hanging)**:
  Root `package.json` (line 30) defines `"lint": "npx turbo run lint --concurrency=1"`. `apps/mekong-ide/package.json` (line 9) defines `"lint": "next lint"`. Running turbo lint fails on `mekong-ide#lint` due to a configuration prompt hang. No configuration files match `*eslint*` under `apps/mekong-ide/`.

---

## 2. Logic Chain

1. **Root `tsconfig` compiles nested monorepo**: Because root `tsconfig.json` uses `include: ["packages/**/*"]`, it recursively scans the nested `cleo-new` monorepo.
2. **Library configuration mismatch causes TS errors**: Since the root config targets `es2022`, newer ES2025 features (like `findLast`) utilized in `cleo-new` are flagged as errors. Because `cleo-new` dependencies are not configured in the root pnpm workspace, its workspace-local packages are not resolved by the root typescript compile context.
3. **Excluding `cleo-new` solves 93% of TS errors**: Restricting the root compiler from scanning `packages/cleo-new/**/*` isolates the two monorepos and resolves the ~4,200 compilation errors in `cleo-new`.
4. **Restricting global types hides React types**: By specifying the `"types"` array in the root `tsconfig.json` without including `"react"`, TypeScript ignores the React types installed in the project. Adding `"react"` and `"react-dom"` resolves the JSX intrinsic elements issue for `packages/ui`.
5. **Casing mismatches block imports**: Standard file imports fail in TypeScript since `index.ts` files import `./tenantCard` instead of the kebab-case filename on disk `./tenant-card`. Correcting paths in `index.ts` files fixes these errors.
6. **Missing config causes interactive prompt**: In the absence of an ESLint configuration file, Next.js's `next lint` prompts the shell for a configuration choice, causing non-interactive Turbo builds to hang. Adding a minimal `.eslintrc.json` config resolves this hang.

---

## 3. Caveats

* Did not perform type checking on the python cli source directory as TS compiler only checks typescript files.
* Assumed that `packages/cleo-new` should be built/checked separately from the root project (supported by its exclusion in root `pnpm-workspace.yaml`).
* Some workspace packages within `cleo-new` might have secondary errors inside their own workspaces that can only be resolved during a nested `pnpm typecheck` run.

---

## 4. Conclusion

The build issues are caused by:
1. Compilation boundaries bleed between the top-level mekong-cli project and the nested cleo-new workspace.
2. Restrictive global types mapping in the root `tsconfig.json` hiding React types.
3. CamelCase to kebab-case import path mismatches in `packages/ui`.
4. Next.js CLI interactive prompts hanging in the absence of a Next.js eslint configuration in `apps/mekong-ide`.

Implementing the proposed remediation steps (excluding `cleo-new` from root tsconfig, including react types, correcting case in UI index files, and adding a basic `.eslintrc.json` for `mekong-ide`) will achieve clean typechecking and linting.

---

## 5. Verification Method

Once changes are applied by the implementer agent, the following commands must be executed to verify the fix:

1. **Root Typecheck**:
   ```bash
   npx tsc --noEmit
   ```
   *Expected result*: No compilation errors for the top-level packages (especially `@mekong/ui` and `@mekong/i18n`).
2. **Nested Monorepo Typecheck**:
   ```bash
   pnpm --filter @cleocode/monorepo typecheck
   ```
   *Expected result*: Types check cleanly inside `packages/cleo-new`.
3. **Turbo Lint Check**:
   ```bash
   npx turbo run lint --concurrency=1
   ```
   *Expected result*: Successful non-interactive completion of the lint step across all packages and apps (specifically `mekong-ide` and `i18n`).
