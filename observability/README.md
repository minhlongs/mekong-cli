# Mekong CLI — Observability Stack

Self-hosted Prometheus + Grafana + OTel Collector on M1 Max.
Grafana exposed at `https://grafana.m1max.cashclaw.cc` via existing CF Tunnel.

## Bring Up (run on M1 Max)

```bash
# 1. SSH into M1 Max
ssh m1max-cf

# 2. Copy secrets template and set admin password
cd ~/mekong-cli/observability
cp .env.observability.template .env.observability
nano .env.observability   # set GF_SECURITY_ADMIN_PASSWORD

# 3. Start stack
docker compose -f docker-compose.observability.yml up -d

# 4. Verify all 3 containers running
docker compose -f docker-compose.observability.yml ps
```

Expected output: `mekong_otel_collector`, `mekong_prometheus`, `mekong_grafana` all `Up`.

## CF Tunnel Route

Add to `~/.cloudflared/config.yml` on M1 Max:

```yaml
ingress:
  - hostname: grafana.m1max.cashclaw.cc
    service: http://localhost:3000
  # ... existing rules ...
```

Then restart: `sudo launchctl kickstart -k system/com.cloudflare.cloudflared`

## GPU Probe — powermetrics Setup

`gpu_probe.py` reads `/tmp/mekong_gpu_metrics.json`. Create a LaunchAgent that writes it:

```bash
# /usr/local/bin/mekong-gpu-sampler.sh
#!/bin/bash
while true; do
  sudo powermetrics --samplers gpu_power -i 10000 -n 1 --output-format json \
    2>/dev/null > /tmp/mekong_gpu_metrics.json
  sleep 10
done
```

Add sudo rule (`/etc/sudoers.d/mekong-powermetrics`):
```
yourusername ALL=(root) NOPASSWD: /usr/bin/powermetrics
```

## OTel Endpoint

Agents send metrics to `localhost:4317` (gRPC). Set env var:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

Or in `.env`: `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`

## Dashboards

Three dashboards auto-provisioned on Grafana startup:
- **Agent Orchestration Performance** — latency p50/p95, drift score, invocation count
- **Token Cost Analysis** — USD/day, USD/month, cost by agent
- **M1 Max Host Health** — GPU util, retry pressure, invocation rate

## Retention

Prometheus: 30-day / 5 GB cap (whichever hit first). Configured in `docker-compose.observability.yml`.
