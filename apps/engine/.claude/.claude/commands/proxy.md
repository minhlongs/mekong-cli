# /proxy command

Manage and monitor the Antigravity Proxy for non-stop agentic coding.

## Usage

- `/proxy:status`: View current account health, rate limits, and model fallback state.
- `/proxy:reset`: Perform a surgical reset of all 429 rate-limit flags to force-resume work.
- `/proxy:start`: Initialize the proxy with the `--fallback` smart routing enabled.

## Implementation Details

The `/proxy` suite interacts with the `antigravity-claude-proxy` engine and the Mekong-CLI specific recovery scripts.

### Recovery Workflow

When the CC CLI reports a quota exhaustion error (400/429):

1. Run `/proxy:reset`.
2. Wait 2 seconds for the service to reload.
3. Send an empty newline `\n` to kickstart the session.

### Strategic Fallback

The proxy is configured to automatically use `gemini-3-pro-high` as a failover for `claude-sonnet-4-5-thinking`. This is managed via the `start-proxy.sh` script using the `--fallback` flag.
