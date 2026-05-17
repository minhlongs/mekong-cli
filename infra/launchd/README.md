# launchd — macOS Boot-Time Services

LaunchDaemon templates for persistent system services (run at boot, restart on crash, survive logout).

## Available

| File | Service |
|------|---------|
| `com.cloudflare.cloudflared.plist` | Cloudflare tunnel template (placeholders interpolated by installer) |
| `install-cloudflared.sh` | Cloudflared installer |
| `com.mekong.gateway.plist` | Mekong Gateway (uvicorn) template — includes `MEKONG_ADMIN_TOKEN` env var |
| `install-mekong-gateway.sh` | Gateway installer (auto-generates 32-byte URL-safe token if `~/.mekong/admin-token.txt` missing) |

## Why LaunchDaemon (not `brew services`)

`brew services start cloudflared` registers a **user-level LaunchAgent** that dies when the user logs out or the machine reboots before login. A **system-level LaunchDaemon** in `/Library/LaunchDaemons/` runs as root from boot and survives all session changes — required for headless tunnels (gateway, SSH, webhook endpoints).

## Install cloudflared

Prereqs:
- `cloudflared` binary at `/opt/homebrew/bin/cloudflared` (`brew install cloudflared`)
- `~/.cloudflared/config.yml` with `tunnel: <UUID>` and ingress rules
- `~/.cloudflared/<UUID>.json` credentials file

Run:
```bash
# Auto-detect tunnel ID from config.yml
./infra/launchd/install-cloudflared.sh

# Or specify tunnel ID explicitly
./infra/launchd/install-cloudflared.sh 35d5d11a-d15d-4fd6-83f3-5ccd6064a569
```

What the installer does:
1. Validates `cloudflared` binary exists
2. Resolves tunnel UUID (arg → config.yml fallback)
3. Backs up existing plist to `*.bak-YYMMDD-HHMMSS` (if any)
4. Interpolates `__USER_HOME__` + `__TUNNEL_ID__` placeholders
5. Installs to `/Library/LaunchDaemons/` with `root:wheel` ownership, mode 644
6. `launchctl bootout` (cleanup) → `bootstrap` (register) → `kickstart -k` (start)
7. Verifies via `launchctl list`

## Install Mekong Gateway

Prereqs:
- Python venv at `<project>/.venv` with FastAPI + uvicorn installed
- `python3` (system) for token generation

Run:
```bash
# Auto-detect project dir (templates lives in <project>/infra/launchd/)
./infra/launchd/install-mekong-gateway.sh

# Or specify project dir explicitly
./infra/launchd/install-mekong-gateway.sh /Users/macbook/mekong-cli
```

What the installer does:
1. Resolves project dir (arg → `$(dirname $0)/../..` fallback)
2. Validates `.venv/bin/uvicorn` binary exists
3. **Token handling:**
   - If `~/.mekong/admin-token.txt` exists → reuses it
   - Else → generates fresh `secrets.token_urlsafe(32)` (43-char URL-safe), saves with mode 600
4. Interpolates `__USER_HOME__` + `__PROJECT_DIR__` + `__MEKONG_ADMIN_TOKEN__` placeholders
5. `plutil -lint` validates generated XML before install
6. Backs up existing plist to `*.bak-YYMMDD-HHMMSS` (if any)
7. Installs to `/Library/LaunchDaemons/` with `root:wheel` ownership, mode 644
8. `bootout` → `bootstrap` → `kickstart -k`
9. Verifies via `launchctl list`

## Verify

```bash
# Cloudflared
sudo launchctl list | grep cloudflared
curl -sI https://YOUR_TUNNEL_HOSTNAME | head -3
tail -20 /Library/Logs/com.cloudflare.cloudflared.err.log

# Mekong Gateway
sudo launchctl list | grep mekong
curl -s http://localhost:8000/healthz                  # local
curl -s https://gateway.cashclaw.cc/healthz            # via tunnel
tail -20 /var/log/mekong-gateway-err.log

# Test admin gate (Round 7+)
TOKEN=$(cat ~/.mekong/admin-token.txt)
curl -X POST https://gateway.cashclaw.cc/v1/pilot/convert \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"opc_999_test","tier":"starter","monthly_vnd":199000}'
# Expect: 404 (unknown user) → auth passed
```

## Uninstall

```bash
# Cloudflared
sudo launchctl bootout system /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo rm /Library/LaunchDaemons/com.cloudflare.cloudflared.plist

# Mekong Gateway
sudo launchctl bootout system /Library/LaunchDaemons/com.mekong.gateway.plist
sudo rm /Library/LaunchDaemons/com.mekong.gateway.plist
# Token stays in ~/.mekong/admin-token.txt — clean manually if rotating: rm ~/.mekong/admin-token.txt
```

## Plist Settings Explained

| Key | Value | Effect |
|-----|-------|--------|
| `RunAtLoad` | `<true/>` | Start service immediately when daemon loaded (boot or bootstrap) |
| `KeepAlive` | `<true/>` | **Unconditional** restart on any exit (success or failure). Required for tunnel + API resilience. |
| `ThrottleInterval` | `10` | Minimum 10s between restart attempts — prevents tight crash loops |
| `StandardOutPath` / `StandardErrorPath` | `/Library/Logs/...` or `/var/log/...` | System log location (vs `/tmp` which clears on boot) |
| `EnvironmentVariables` | dict | Inject env at launchd-process level. **SIP blocks `launchctl setenv`** — must edit plist directly. |

## Token Rotation

```bash
# 1. Delete existing token
rm ~/.mekong/admin-token.txt

# 2. Re-run installer (generates fresh token)
./infra/launchd/install-mekong-gateway.sh

# 3. Distribute new token to admin clients (Zalo bot, dashboard, etc.)
cat ~/.mekong/admin-token.txt
```

## Pitfall — Original Cloudflared Bug (2026-05-17)

The initial install via `brew services` or `sudo cloudflared service install` registered a plist with:

```xml
<key>ProgramArguments</key>
<array>
  <string>/opt/homebrew/bin/cloudflared</string>
</array>
```

Missing the `tunnel`, `--config`, and `run <UUID>` subcommand args. Result: cloudflared launched, printed help text, exited with status 0. With `KeepAlive` set to `{SuccessfulExit: false}`, exit 0 was treated as "done" → service never restarted → tunnel never reached active state after reboot. Symptom: `gateway.cashclaw.cc` returned Cloudflare 1033 error (no active connectors).

This template prevents recurrence by:
1. Including the full `tunnel … run <UUID>` argv
2. Setting `KeepAlive` to unconditional `<true/>`

## Pitfall — SIP Blocks `launchctl setenv` (2026-05-17, Round 7)

Attempted to inject `MEKONG_ADMIN_TOKEN` via `sudo launchctl setenv MEKONG_ADMIN_TOKEN <value>` failed with:

```
150: Operation not permitted while System Integrity Protection is engaged.
```

Workaround applied: edit `/Library/LaunchDaemons/com.mekong.gateway.plist` directly to add the token inside the `EnvironmentVariables` dict, then `bootout` → `bootstrap` → `kickstart -k`. This template now bakes that pattern in — `install-mekong-gateway.sh` interpolates the token at install time so SIP is never in the path.

## Notes

- Plists are **root-owned, system-scoped** — survive user logout, run from boot
- `tunnel run` (not `tunnel start`) is the long-running cloudflared subcommand
- Tunnel credentials (`~/.cloudflared/<UUID>.json`) must be readable by root — owned by user is fine since LaunchDaemon reads via absolute path
- `~/.mekong/admin-token.txt` is mode 600, never committed (`.mekong/` is in `~/`, not in repo)
- If you rotate tunnel UUID or admin token, re-run respective installer with fresh value
