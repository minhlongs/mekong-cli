# OpenClaw Bridge — Cloudflare Tunnel Setup

> Connect the local Mekong CLI to the cloud via Cloudflare Tunnel.
> **Pattern:** Cloud Ra Lenh + Local Thuc Thi (Hybrid Commander)

## Prerequisites

- Mekong CLI installed locally
- Cloudflare account with Zero Trust access
- `cloudflared` CLI installed (`brew install cloudflared`)

## Architecture

```
[Telegram/Web] → [OpenClaw on CF Workers] → [Cloudflare Tunnel] → [Mac: Mekong Gateway :8000]
```

## Step 1: Set API Token

```bash
export MEKONG_API_TOKEN="your-secret-token-here"
```

Add to `~/.zshrc` or `~/.bashrc` for persistence.

## Step 2: Start the Gateway

```bash
# Default: localhost:8000
mekong gateway

# Custom port/host
mekong gateway --port 9000 --host 0.0.0.0
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.2.0","engine":"Plan-Execute-Verify"}
```

## Step 3: Create Cloudflare Tunnel

```bash
# Login to Cloudflare
cloudflared tunnel login

# Create a named tunnel
cloudflared tunnel create mekong-bridge

# Route DNS (replace with your domain)
cloudflared tunnel route dns mekong-bridge mekong.yourdomain.com
```

## Step 4: Configure the Tunnel

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: mekong-bridge
credentials-file: ~/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: mekong.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

## Step 5: Run the Tunnel

```bash
cloudflared tunnel run mekong-bridge
```

## Step 6: Test Remote Execution

From anywhere in the world:

```bash
curl -X POST https://mekong.yourdomain.com/cmd \
  -H "Content-Type: application/json" \
  -d '{"goal": "list all git branches", "token": "your-secret-token-here"}'
```

## Security Notes

- **MEKONG_API_TOKEN** is the only auth gate — use a strong random token
- Cloudflare Tunnel encrypts traffic end-to-end (no port forwarding needed)
- Tunnel credentials are stored locally in `~/.cloudflared/`
- Consider Cloudflare Access policies for additional protection

## Integration with OpenClaw (CF Worker)

The OpenClaw Worker forwards Telegram commands to this gateway:

```javascript
// In your CF Worker (apps/raas-gateway/index.js)
const response = await fetch('https://mekong.yourdomain.com/cmd', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    goal: userMessage,
    token: env.MEKONG_API_TOKEN,
  }),
});
```

## Tags

- openclaw
- gateway
- cloudflare
- tunnel
- remote
