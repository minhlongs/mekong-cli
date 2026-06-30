# agy (Antigravity) CLI Integration Guide

The `agy` CLI replaces the retired `gemini` CLI (Google retired the `gemini`
binary on 2026-06-18). `agy` runs MCP servers in print (headless) mode, accepts
the same `gemini-*` model ids, and is the primary path for `/ck:use-mcp`.

## Model Configuration

Read the model id from `$HOME/.claude/.ck.json`: `gemini.model` (default:
`gemini-3-flash-preview`). The `.ck.json` key is intentionally still named
`gemini` — `agy` accepts every `gemini-*` model id, so existing user configs keep
working unchanged.

## Installation

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

Verify installation:
```bash
agy --version
```

If `agy` is not on `PATH` after install, it is typically at `~/.local/bin/agy`.

## MCP Configuration (mcp_config.json, NOT a settings.json symlink)

`agy` does **not** read `.gemini/settings.json`, and it does **not** read MCP
servers from the workspace `.agents/` folder (`.agents/` holds agent metadata —
plans, progress, handoffs — only). Verified empirically: `agy` loads MCP servers
from the **global** config at `~/.gemini/config/mcp_config.json` in print mode.

The file shape matches `$HOME/.claude/.mcp.json` (`{"mcpServers": {...}}`), so the
project's servers are merged into the global file:

```bash
# Merge project MCP servers ($HOME/.claude/.mcp.json) into agy's global mcp_config.json
GLOBAL=~/.gemini/config/mcp_config.json
mkdir -p ~/.gemini/config
[ -f "$GLOBAL" ] || echo '{"mcpServers":{}}' > "$GLOBAL"
node -e '
  const fs=require("fs"),os=require("os"),path=require("path");
  const g=path.join(os.homedir(),".gemini/config/mcp_config.json");
  const proj=JSON.parse(fs.readFileSync("$HOME/.claude/.mcp.json","utf8"));
  const cur=JSON.parse(fs.readFileSync(g,"utf8"));
  cur.mcpServers={...(cur.mcpServers||{}),...(proj.mcpServers||{})};
  fs.writeFileSync(g,JSON.stringify(cur,null,2));
  console.log("merged servers:",Object.keys(cur.mcpServers).join(", "));
'
```

A server entry uses the standard MCP shape:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    }
  }
}
```

Use `$VAR_NAME` in `env` values for secrets (e.g. `"BRAVE_API_KEY": "$BRAVE_API_KEY"`).
Keep `~/.gemini/config/mcp_config.json` out of version control if it holds secrets.

## Usage

### Print mode + prepended contract (MCP tasks)

`agy` has no auto-loaded system-prompt file, so `/ck:use-mcp` prepends the JSON
proxy contract (`references/mcp-proxy-contract.md`) into the piped prompt:

```bash
printf '%s\n\nTASK: %s' "$CONTRACT" "<task>" \
  | agy --dangerously-skip-permissions --model <gemini.model> -p
```

### Essential flags

- `--dangerously-skip-permissions` — auto-approve all tool permission requests
  (the `agy` equivalent of the old `gemini -y` / `--yolo`).
- `--model <id>` — model selection (`gemini-2.5-flash`, `gemini-3-flash-preview`,
  `gemini-2.5-pro`, etc.). All verified working with `agy`.
- `-p` / `--print` / `--prompt` — run a single prompt non-interactively and print
  the response. Required for headless runs (stdin-piped or inline).
- `--print-timeout <dur>` — native timeout for print mode (default `5m0s`). Use
  e.g. `--print-timeout 120s` instead of wrapping the call in a shell `timeout`.

### Inline vs stdin

Both forms work in print mode:

```bash
# Inline
agy --dangerously-skip-permissions --model <gemini.model> -p "<task>"

# Stdin (preferred when prepending the multi-line contract)
printf '%s\n\nTASK: %s' "$CONTRACT" "<task>" | agy --dangerously-skip-permissions --model <gemini.model> -p
```

## Error Handling

When `agy` fails, check exit code and output for known error markers:
```bash
RESULT=$(printf '%s\n\nTASK: %s' "$CONTRACT" "task" | agy --dangerously-skip-permissions --model <gemini.model> -p 2>&1)
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ] || echo "$RESULT" | grep -q "GaxiosError\|RESOURCE_EXHAUSTED\|MODEL_CAPACITY_EXHAUSTED\|PERMISSION_DENIED\|UNAUTHENTICATED"; then
  echo "[AGY_UNAVAILABLE] Falling back to script execution."
  # Use Path 2 (direct scripts in scripts/cli.ts) as the fallback path
else
  echo "$RESULT"
fi
```

Common failure modes:
- **429 `MODEL_CAPACITY_EXHAUSTED`**: model overloaded. Try `gemini-2.5-flash`.
- **429 `RESOURCE_EXHAUSTED`**: rate limit. Wait and retry, or switch to scripts.
- **403 `PERMISSION_DENIED`**: account tier doesn't support the model, or auth expired.
- **401 `UNAUTHENTICATED`**: token invalid/expired. Re-authenticate (launch `agy`
  with no arguments to sign in).
- **Timeout**: print-mode wait exceeded `--print-timeout`. Reduce prompt
  complexity, raise the timeout, or switch model.

## How It Works

1. **Configuration loading**: `agy` reads MCP servers from `~/.gemini/config/mcp_config.json`.
2. **Server connection**: connects to all configured MCP servers in print mode.
3. **Tool discovery**: lists available tools from servers.
4. **Prompt analysis**: the model reads the prepended contract + task.
5. **Tool selection**: selects relevant tools.
6. **Execution**: calls tools with appropriate parameters.
7. **Result synthesis**: returns the single-line JSON per the contract.

## Verifying MCP is loaded

```bash
# Quick check — lists servers agy can see in print mode
echo "List the MCP server names available to you. Return ONLY a JSON array of names." \
  | agy --dangerously-skip-permissions -p --print-timeout 120s
```

If the array is empty, confirm `~/.gemini/config/mcp_config.json` has your servers
and that `agy` is authenticated.

## Comparison with Alternatives

| Method | Speed | Flexibility | Setup | Best For |
|--------|-------|-------------|-------|----------|
| agy CLI | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | All tasks |
| Direct Scripts | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Specific tool, deterministic invocation |

**Recommendation**: use `agy` as the primary method, fall back to
`scripts/cli.ts call-tool` when unavailable.

## Resources

- [Antigravity CLI install](https://antigravity.google/cli/install.sh)
- `references/configuration.md` — `.mcp.json` schema, env file lookup order
- `references/mcp-protocol.md` — JSON-RPC details, transports, error codes
- `references/mcp-proxy-contract.md` — the JSON contract `/ck:use-mcp` prepends
