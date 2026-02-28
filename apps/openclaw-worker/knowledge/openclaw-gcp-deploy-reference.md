# OpenClawGCP — Cloud Deployment Reference

> Source: github.com/lktiep/OpenClawGCP (@lktiep 🇻🇳)
> Classification: REFERENCE — Cloud deployment guide
> Date: 2026-02-18

## 10-Phase Deploy Flow

1. GCP VM (project + VM + SSH)
2. Docker setup
3. Deploy OpenClaw (clone + run + port 18789)
4. CLIProxyAPI (LLM proxy on port 8317)
5. Cloudflare Tunnel (remote access)
6. Cloudflare Access + Google SSO
7. OpenClaw Config (gateway + env vars)
8. Vertex AI + Python packages
9. Multi-Agent Setup (multiple Telegram bots)
10. Access & Verification

## Multi-Agent Config Template

```json
{
  "agents": {
    "list": [
      { "id": "main",   "name": "Javis",  "model": "proxypal/claude-opus-4-5-thinking" },
      { "id": "lena",   "name": "Lena",   "model": "proxypal/gemini-3-pro-high" },
      { "id": "marcus", "name": "Marcus", "model": "proxypal/gemini-3-pro-high" }
    ]
  },
  "tools": {
    "agentToAgent": { "enabled": true, "allow": ["main", "lena", "marcus"] }
  }
}
```

## Key Gotchas

- Use `proxypal/<model>` NOT `anthropic/<model>` for proxy
- `agentToAgent` uses `enabled` + `allow`, NOT `allowAny`
- `trustedProxies` required for Cloudflare Tunnel
- Agent YAML per-agent: systemPrompt, model, tools

## Quick Commands

```bash
# SSH
gcloud compute ssh openclaw-gateway --zone=<ZONE>

# Logs
sudo docker logs openclaw-openclaw-gateway-1 --since 5m

# Restart
cd ~/openclaw && sudo docker compose restart openclaw-gateway

# Nuclear reset
sudo docker compose down && sudo docker compose up -d
```
