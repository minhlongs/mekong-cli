---
name: careful-mode
description: Block destructive commands when working with production systems. Activate with /careful. Blocks rm -rf, DROP TABLE, force-push, docker rm, kubectl delete, and Polymarket order placement in LIVE mode. Deactivate with /careful-off.
---

# Careful Mode

## Overview
On-demand safety hook. Blocks destructive operations via PreToolUse matcher on Bash.

## Activation
```
/careful      — Enable destructive command blocking
/careful-off  — Disable (returns to normal mode)
```

## Blocked Patterns
When active, these commands are BLOCKED with a warning:
- `rm -rf` / `rm -r` (outside /tmp)
- `DROP TABLE` / `DROP DATABASE` / `TRUNCATE`
- `git push --force` / `git push -f`
- `docker rm` / `docker rmi` / `docker system prune`
- `kubectl delete`
- Any command containing `CASHCLAW_MODE=LIVE` (prevents accidental live trading)
- `wrangler delete` / `wrangler d1 delete`

## Hook Configuration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "scripts/careful-check.sh"
          }
        ]
      }
    ]
  }
}
```

## Scripts
- `scripts/careful-check.sh` — Receives the bash command, exits 1 if destructive

## Gotchas
- This is an ON-DEMAND hook. Don't enable by default — it would block legitimate operations.
- The check is substring-based. False positives possible for commands that mention "rm" in filenames.
- Does NOT block API calls made via curl/httpx. Only blocks direct bash commands.
