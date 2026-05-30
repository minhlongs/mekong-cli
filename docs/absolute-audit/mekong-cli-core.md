# Subsystem Audit: packages/mekong-cli-core

## 1. Purpose
- **Business Role**: Serves as the AI-operated business platform CLI engine (ROIaaS - Return on Investment as a Service) containing command definitions (319 commands across 5 levels), license gatekeeping, and task orchestration boundaries.
- **Technical Role**: Implements Commander-based CLI parsing, ReAct agent loops, constraint verification, persistence rules (session logs), and third-party SaaS payment/calendar integrations.

## 2. Entry Points
- **CLI Bootstrapper**: `src/cli/index.ts`.
- **Core Library Export**: `src/core/index.ts`.
- **PEV Loop**: `src/core/pev-bridge.ts` (Plan-Execute-Verify).

## 3. Runtime Lifecycle
- **Step-by-Step Dispatch**:
  1. Command invoked.
  2. PreAction hook initializes `MekongEngine` (registers shell, git, file, and http tools; instantiates OpenClawEngine).
  3. PreAction hook intercepts command and validates license tier via `LicenseGate`.
  4. If validation succeeds, invokes target Commander command.
  5. Fallback commands are parsed and delegated down the ROIaaS hierarchy or executed via ReAct `WorkerAgent` loop.
  6. Final output written to Session memory log.

## 4. State Management
- **Interaction History**: Append-only JSONL files under `~/.mekong/sessions/{sessionId}.jsonl`.
- **Credentials/API Keys**: Persisted in `~/.mekong/credentials.json`.
- **License Keys**: Stored with restricted file permissions (`0o600`) in `~/.mekong/license.json`.
- **In-Memory states**: Task budgets, Cron jobs, pool of active workers.

## 5. Dependencies
- **Internal Workspaces**: `@openclaw/cli-adapter`, `@mekong/ask-core`, `@mekongcli/openclaw-engine`.
- **External Libraries**: `commander`, `cron`, `csv-parse`, `csv-stringify`, `date-fns`, `eventemitter3`, `glob`, `googleapis`, `handlebars`, `ignore`, `markdown-table`, `nodemailer`, `ora`, `p-queue`, `semver`, `simple-statistics`, `stripe`, `tar`, `winston`, `ws`, `yaml`, `zod`, `tsup`.

## 6. Failure Modes
- **LLM Provider Failure**: Throws `LLM_ALL_PROVIDERS_FAILED` if no configured models respond.
- **SOP Loop/Recursion**: Infinite loops in recursive SOP invocations (guarded up to depth 10).
- **PreAction Initialization Failure**: Engine crashes if configuration is malformed or invalid Zod schema.

## 7. Recovery Behavior
- **Automatic LLM Provider Failover**: Rotates through secondary provider configurations on API request failures.
- **SOP Action Fallbacks**: Supports `continue` on fail, `stop`, and retry (based on delay settings).
- **Jidoka rule**: Shuts down agent loops after 3 consecutive failures.
- **License Grace Window**: 7-day grace period before blockages occur on expired keys.

## 8. Scale Limits
- **In-Memory Storage**: Background daemon runs will accumulate active task and event histories in memory without limit checks.
- **Concurrency Gates**: WIP limits restrict agent spawn counts to a default of 3 concurrent instances.

## 9. Security Surface
- **Shell Tool**: Exposes arbitrary bash commands to LLM agents.
- **Weak Shell Sanitization**: The regex blacklist (`rm -rf /`, `sudo`) is easy to bypass.
- **Hardcoded Secret fallback**: HMAC verification uses a fallback secret string (`mekong-license-v1-secret`).

## 10. Observability
- **Event Bus**: Event-emitter3 acts as the internal system-wide event broker.
- **APM Gaps**: `attachObservability` is a template stub function with no real integration.

## 11. Technical Debt
- **Empty Stubs**: `attachObservability` lacks any implementation.
- **Type casting**: Uses `as any` bypasses in session logs and database models.
- **Reactive Pattern Fallback**: The 'reactive' orchestration pattern is unimplemented, falling back directly to sequential execution.

## 12. Missing Knowledge
- **Cloud Metrics Sync**: It is unclear how execution usage limits are dynamically validated against the RaaS dashboard or if it is purely local token estimation.
