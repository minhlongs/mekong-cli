/**
 * Department command data layer.
 * Returns typed mock data matching what apps/ide-ui hardcodes today.
 * When a live API exists, swap the implementation — types stay stable.
 */

import type { DepartmentCommand, ReportPage } from "./types.js";

// ─── Engineering Layer (10 commands, mirrors B1 hardcoded data) ──────────────

const ENGINEERING_COMMANDS: DepartmentCommand[] = [
  {
    slug: "cook",
    title: "Cook — Full Feature Build",
    description:
      "End-to-end feature implementation: plan → code → test → review. Single command ships production code.",
    mcu: 5,
    layer: "engineering",
  },
  {
    slug: "code",
    title: "Code — Targeted Implementation",
    description:
      "Write or modify specific files following existing patterns. Scoped, fast, context-aware.",
    mcu: 2,
    layer: "engineering",
  },
  {
    slug: "review",
    title: "Review — Code Quality Gate",
    description:
      "Static analysis, type safety check, security scan, and style review. Outputs actionable diff.",
    mcu: 2,
    layer: "engineering",
  },
  {
    slug: "test",
    title: "Test — Test Suite Execution",
    description:
      "Run unit + integration tests, report coverage delta, surface regressions with fix hints.",
    mcu: 2,
    layer: "engineering",
  },
  {
    slug: "deploy",
    title: "Deploy — CF Pages / Workers",
    description:
      "Build artifact, run smoke test, deploy to Cloudflare Pages or Workers. Zero-downtime.",
    mcu: 3,
    layer: "engineering",
  },
  {
    slug: "fix",
    title: "Fix — Bug Resolution",
    description:
      "Root-cause analysis from logs or error output, minimal patch, regression test added.",
    mcu: 3,
    layer: "engineering",
  },
  {
    slug: "engineering-new-service",
    title: "New Service — Scaffold Microservice",
    description:
      "Bootstrap a new CF Worker service with D1/KV/R2 bindings, CI pipeline, and wrangler config.",
    mcu: 5,
    layer: "engineering",
  },
  {
    slug: "engineering-refactor",
    title: "Refactor — Codebase Cleanup",
    description:
      "Extract modules, remove tech debt (console.log, any types, TODO), enforce 200-LOC file cap.",
    mcu: 4,
    layer: "engineering",
  },
  {
    slug: "dev-pr-review",
    title: "PR Review — Pull Request Analysis",
    description:
      "Diff analysis, breaking-change detection, migration guide generation, approval recommendation.",
    mcu: 2,
    layer: "engineering",
  },
  {
    slug: "devops-deploy-pipeline",
    title: "Deploy Pipeline — CI/CD Setup",
    description:
      "Generate GitHub Actions workflow: typecheck → test → build → deploy → smoke test chain.",
    mcu: 4,
    layer: "engineering",
  },
];

const DEPARTMENT_MAP: Record<string, DepartmentCommand[]> = {
  engineering: ENGINEERING_COMMANDS,
};

/**
 * Get all commands for a department by slug.
 * Returns empty array for unknown slugs (graceful degradation).
 */
export async function getDepartmentCommands(
  slug: string
): Promise<ReportPage<DepartmentCommand[]>> {
  const data = DEPARTMENT_MAP[slug] ?? [];
  return {
    data,
    fetchedAt: Date.now(),
    source: "mock",
  };
}
