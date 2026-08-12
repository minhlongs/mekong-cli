# Design-Sync Notes — mekong-cli (v6.0)

## Source Shapes
- shape: package
- source package: packages/ui/
- token package: packages/tokens/
- node module resolution: pnpm (node_modules/.pnpm)
- build tool: esbuild 0.24.2

## Build Choices
- Generated .ds-entry.ts as entry point listing all 85 component files (99 displayNames)
- Bundled via esbuild ESM es2020, 250.9kb
- CSS written as raw CSS custom properties (no @apply — Tailwind not available to previews)
- Skipped .d.ts generation — tsc declaration emit not configured for monorepo
- styles.css uses @import to packages/tokens/src/ (needs inlining for upload)

## Known Limitations
1. CSS class syntax uses Tailwind JIT patterns (bg-[var(--Accent)] etc.) — requires Tailwind build step for full rendering
2. Domain components (trading, analytics, sales charts) embed internal data/hooks — render as static shells without runtime
3. CVA (class-variance-authority) merged via tailwind-merge in bundle — standard CSS classes safe; custom var() classes need JIT
4. No React/DOM bundled — environment supplies them
5. `packages/ui/src/styles/tokens.css` is stale duplicate from Pencil.dev; canonical: `packages/tokens/`

## Future Steps (after auth)
1. Run `/design-login` to authorize DesignSync
2. Create/reuse project via DesignSync API
3. Rebuild with Tailwind JIT step for CSS resolution
4. Conventions header after preview verification
5. Incremental upload via DesignSync(finalize_plan)
