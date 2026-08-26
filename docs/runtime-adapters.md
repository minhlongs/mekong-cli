# Runtime Adapters

> Refreshed: 2026-08-26 · Code: `src/core/exec_runtime/`
> (`types.py`, `local.py`), reuse of `src/core/command_sanitizer.py`

`ExecutionRuntime` is the Protocol that isolates *where and how* agent
actions actually run. v0.1 ships exactly one implementation, local-first;
remote runtimes are planned but intentionally not built.

## ExecutionRuntime protocol

| Method | Contract |
|--------|----------|
| `execute(command, *, timeout_s=None) -> ExecResult` | run a command; failures return `ExecResult(ok=False)`, never raise |
| `filesystem()` | facade confined to a root directory (path-traversal safe) |
| `process()` | tracked process control (terminate/kill) |
| `network_policy()` | declared policy struct |
| `environment()` | environment snapshot |
| `preview(request)` | dry-run: what would execute, blocked reasons |
| `health()` | liveness/state report |
| `destroy()` | terminate all tracked processes; execute refuses afterwards |

## LocalExecutionRuntime

- **Subprocess with real timeouts** — `communicate(timeout=...)`, kill +
  reap on expiry; SIGTERM→SIGKILL escalation for cancellation.
- **Shell-shaped commands are sanitized** — string commands pass through
  `CommandSanitizer(strict_mode=True)` first; injection attempts return
  `ExecResult(ok=False, error="blocked by sanitizer: ...")`.
- **Filesystem confinement** — `SandboxSpec.resolve_in_root` resolves then
  verifies the path stays inside the root (symlink-aware). `../../etc/passwd`,
  absolute paths outside the root, and symlink escapes all raise
  `PermissionError`.
- **Network policy is honest about being a placeholder** — default is a
  deny-all struct (`allow_outbound=False`, description "not enforced").
  There is NO enforcement layer yet; do not treat it as a security
  boundary.

## Planned (not built in v0.1)

- **Cloudflare Workers runtime adapter** — would map `ExecutionRuntime`
  onto CF Workers/Containers. Nothing is hard-coded for Cloudflare today.
- **Docker/container runtime adapter** — same protocol over container
  isolation.
- **Real network enforcement** — replace the deny-all placeholder struct
  with an enforced policy.

Both future adapters must satisfy the same structural Protocol; no core
code changes should be needed to adopt them.

## Tests

`tests/test_local_execution_runtime.py` (38 tests): exec success/failure,
stderr capture, timeout kill, cancel/destroy, injection blocking
(`rm -rf /`, chained commands, backticks), path traversal, symlink escape,
policy/env/preview/health, and Protocol conformance.
