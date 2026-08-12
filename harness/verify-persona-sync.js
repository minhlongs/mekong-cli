export const meta = {
  name: 'verify-persona-sync',
  description: 'Verify the dynamic command sync implementation passes typecheck, build, and tests',
  phases: [
    { title: 'Typecheck', detail: 'tsc --noEmit on harness' },
    { title: 'Build', detail: 'npm run build' },
    { title: 'Tests', detail: 'npm test + failure analysis' },
    { title: 'Fix', detail: 'Fix remaining errors' },
  ],
};

// Phase 1: Typecheck
const typecheckResult = await agent(
  'Run TypeScript compiler check on the harness project at /Users/macbook/mekong-cli/harness. Execute: npx tsc --noEmit 2>&1 | head -50. Report ALL errors with file paths and line numbers. Focus especially on errors in: src/personas/personas.ts, src/core/types.ts, src/core/command-router.ts, src/index.ts. If there are zero errors, report "CLEAN".',
  { label: 'typecheck', phase: 'Typecheck', effort: 'high' }
);

log('Typecheck complete, building...');

// Phase 2: Build
const buildResult = await agent(
  'Run the production build for the harness project. Execute: cd /Users/macbook/mekong-cli/harness && npm run build 2>&1 | tail -30. Report any build errors. If build succeeds with exit 0, report "BUILD OK".',
  { label: 'build', phase: 'Build', effort: 'high' }
);

log('Build complete, running tests...');

// Phase 3: Tests
const testResult = await agent(
  'Run the test suite. Execute: cd /Users/macbook/mekong-cli/harness && npm test 2>&1 | tail -50. Report pass/fail counts, any failing tests with error messages. If all tests pass, report "ALL TESTS PASS".',
  { label: 'tests', phase: 'Tests', effort: 'high' }
);

log('Tests complete, analyzing failures...');

// Phase 4: Fix any remaining errors
const fixResult = await agent(
  `Based on the typecheck, build, and test results, fix ALL remaining errors in priority order: (1) TypeScript type errors, (2) Build errors, (3) Failing tests. For each error: identify root cause, implement minimal fix, verify fix doesn't introduce new errors. Use Edit tool for surgical changes. Do NOT rewrite entire files. Constraints: preserve all existing APIs, do not add new dependencies, do not change test expectations unless they were testing the old hardcoded behavior.`,
  { label: 'fix', phase: 'Fix', effort: 'xhigh' }
);

return {
  typecheck: typecheckResult,
  build: buildResult,
  tests: testResult,
  fix: fixResult,
};
