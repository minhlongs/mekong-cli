# launchd — macOS Boot-Time Services

LaunchDaemon templates for persistent system services (run at boot, restart on crash, survive logout).

## Available

| File | Service |
|------|---------|
| `com.cloudflare.cloudflared.plist` | Cloudflare tunnel template (placeholders interpolated by installer) |
| `install-cloudflared.sh` | Installer: validates binary, interpolates placeholders, bootstraps service |

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

## Verify

```bash
sudo launchctl list | grep cloudflared
# Expected: PID + 0 exit status

curl -sI https://YOUR_TUNNEL_HOSTNAME | head -3
# Expected: HTTP/2 200 (or 502 if upstream down — but tunnel itself OK)

tail -20 /Library/Logs/com.cloudflare.cloudflared.err.log
# Look for: "Registered tunnel connection" lines
```

## Uninstall

```bash
sudo launchctl bootout system /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
sudo rm /Library/LaunchDaemons/com.cloudflare.cloudflared.plist
# (Backups under *.bak-* remain — clean manually if desired)
```

## Plist Settings Explained

| Key | Value | Effect |
|-----|-------|--------|
| `RunAtLoad` | `<true/>` | Start service immediately when daemon loaded (boot or bootstrap) |
| `KeepAlive` | `<true/>` | **Unconditional** restart on any exit (success or failure). Required for tunnel resilience. |
| `ThrottleInterval` | `10` | Minimum 10s between restart attempts — prevents tight crash loops |
| `StandardOutPath` / `StandardErrorPath` | `/Library/Logs/...` | System log location (vs `/tmp` which clears on boot) |

## Pitfall — Original Bug (2026-05-17)

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

## Notes

- Plist is **root-owned, system-scoped** — survives user logout, runs from boot
- `tunnel run` (not `tunnel start`) is the long-running daemon subcommand
- Tunnel credentials (`~/.cloudflared/<UUID>.json`) must be readable by root — owned by user is fine since LaunchDaemon reads via absolute path
- If you rotate tunnel UUID, re-run installer with the new UUID
