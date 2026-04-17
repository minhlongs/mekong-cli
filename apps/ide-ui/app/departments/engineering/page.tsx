import { ArrowLeft } from "lucide-react";
import { DeptCommandList, type DeptCommand } from "@/components/dept-command-list";
import { MD3Button } from "@/components/md3-button";

// Static command data derived from .claude/commands/ at build time.
// Pattern: mekong /cook, /code, /deploy etc. — 10 engineering workflows.
const ENGINEERING_COMMANDS: DeptCommand[] = [
  {
    slug: "cook",
    title: "Cook — Full Feature Build",
    description:
      "End-to-end feature implementation: plan → code → test → review. Single command ships production code.",
    mcu: 5,
  },
  {
    slug: "code",
    title: "Code — Targeted Implementation",
    description:
      "Write or modify specific files following existing patterns. Scoped, fast, context-aware.",
    mcu: 2,
  },
  {
    slug: "review",
    title: "Review — Code Quality Gate",
    description:
      "Static analysis, type safety check, security scan, and style review. Outputs actionable diff.",
    mcu: 2,
  },
  {
    slug: "test",
    title: "Test — Test Suite Execution",
    description:
      "Run unit + integration tests, report coverage delta, surface regressions with fix hints.",
    mcu: 2,
  },
  {
    slug: "deploy",
    title: "Deploy — CF Pages / Workers",
    description:
      "Build artifact, run smoke test, deploy to Cloudflare Pages or Workers. Zero-downtime.",
    mcu: 3,
  },
  {
    slug: "fix",
    title: "Fix — Bug Resolution",
    description:
      "Root-cause analysis from logs or error output, minimal patch, regression test added.",
    mcu: 3,
  },
  {
    slug: "engineering-new-service",
    title: "New Service — Scaffold Microservice",
    description:
      "Bootstrap a new CF Worker service with D1/KV/R2 bindings, CI pipeline, and wrangler config.",
    mcu: 5,
  },
  {
    slug: "engineering-refactor",
    title: "Refactor — Codebase Cleanup",
    description:
      "Extract modules, remove tech debt (console.log, any types, TODO), enforce 200-LOC file cap.",
    mcu: 4,
  },
  {
    slug: "dev-pr-review",
    title: "PR Review — Pull Request Analysis",
    description:
      "Diff analysis, breaking-change detection, migration guide generation, approval recommendation.",
    mcu: 2,
  },
  {
    slug: "devops-deploy-pipeline",
    title: "Deploy Pipeline — CI/CD Setup",
    description:
      "Generate GitHub Actions workflow: typecheck → test → build → deploy → smoke test chain.",
    mcu: 4,
  },
];

export default function EngineeringDeptPage() {
  return (
    <main
      className="min-h-screen"
      style={{ background: "var(--md-sys-color-background)" }}
    >
      {/* Nav */}
      <nav
        className="w-full px-6 py-4 flex items-center justify-between border-b border-[var(--md-sys-color-outline)]"
        style={{ background: "var(--md-sys-color-surface)" }}
      >
        <span
          className="m3-title-medium"
          style={{ color: "var(--md-sys-color-primary)" }}
        >
          Mekong IDE
        </span>
        <a
          href="https://github.com/longtho638-jpg/mekong-cli"
          target="_blank"
          rel="noreferrer"
          className="m3-label-large transition-opacity hover:opacity-70"
          style={{ color: "var(--md-sys-color-on-surface-variant)" }}
        >
          GitHub
        </a>
      </nav>

      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Back */}
        <MD3Button variant="text" href="/" className="mb-8 -ml-2">
          <ArrowLeft size={18} />
          Back to Home
        </MD3Button>

        {/* Header */}
        <div className="mb-10">
          <p
            className="m3-label-large mb-2"
            style={{ color: "var(--md-sys-color-primary)" }}
          >
            Department
          </p>
          <h1
            className="m3-headline-large mb-4"
            style={{ color: "var(--md-sys-color-on-background)" }}
          >
            Engineering Layer
          </h1>
          <p
            className="m3-body-large max-w-2xl"
            style={{ color: "var(--md-sys-color-on-surface-variant)" }}
          >
            {ENGINEERING_COMMANDS.length} commands that plan, build, test, review, and
            deploy code autonomously. From a single feature to a full microservice
            — agents handle the entire engineering lifecycle.
          </p>
        </div>

        {/* Stats row */}
        <div className="flex flex-wrap gap-6 mb-10">
          {[
            { label: "Commands", value: String(ENGINEERING_COMMANDS.length) },
            { label: "Min MCU", value: "2" },
            { label: "Max MCU", value: "5" },
            { label: "Deploy target", value: "CF Pages" },
          ].map((stat) => (
            <div
              key={stat.label}
              className="flex flex-col gap-1 px-5 py-3 rounded-[var(--md-sys-shape-corner-medium)]"
              style={{ background: "var(--md-sys-color-surface-variant)" }}
            >
              <span
                className="m3-headline-small"
                style={{ color: "var(--md-sys-color-primary)" }}
              >
                {stat.value}
              </span>
              <span
                className="m3-label-medium"
                style={{ color: "var(--md-sys-color-on-surface-variant)" }}
              >
                {stat.label}
              </span>
            </div>
          ))}
        </div>

        {/* Command list */}
        <DeptCommandList commands={ENGINEERING_COMMANDS} />

        {/* CTA */}
        <div
          className="mt-12 p-8 rounded-[var(--md-sys-shape-corner-large)] text-center"
          style={{ background: "var(--md-sys-color-surface-variant)" }}
        >
          <h2
            className="m3-headline-small mb-3"
            style={{ color: "var(--md-sys-color-on-surface)" }}
          >
            Start using Engineering Layer
          </h2>
          <p
            className="m3-body-medium mb-6"
            style={{ color: "var(--md-sys-color-on-surface-variant)" }}
          >
            200 credits/mo at Starter tier — enough for 40+ engineering missions.
          </p>
          <MD3Button
            href="https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA"
            target="_blank"
            rel="noreferrer"
          >
            Subscribe — $49/mo
          </MD3Button>
        </div>
      </div>
    </main>
  );
}
