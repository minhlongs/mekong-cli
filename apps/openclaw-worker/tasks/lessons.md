# Lessons Learned

## 2026-02-25 - Vite/Vitest Server Hanging in Cloudflare Workers
- **Issue**: Running `npm test` using `@cloudflare/vitest-pool-workers` would pass the tests but the vite server would hang indefinitely, preventing the test process from exiting correctly.
- **Root Cause**: The default Vitest runner in a Cloudflare workers context sometimes leaves orphaned handles (like file watchers or fetch streams in Miniflare).
- **Solution**: Changed the vitest test pool to `'forks'` and added `isolatedStorage: true` inside `vitest.config.ts`. This ensures each test process is properly isolated and torn down after completion, bypassing the hanging vite server issue. Also added `main: './src/index.ts'` to explicitly define the worker entry point, and configured the missing assets binding in `wrangler.jsonc` that was throwing a warning.