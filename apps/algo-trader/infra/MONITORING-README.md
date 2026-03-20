# Algo-Trader Monitoring Infrastructure

Complete monitoring stack for Algo-Trader with Prometheus, Grafana, and Alertmanager.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Algo-Trader Stack                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐     ┌──────────────┐     ┌─────────────────────────────┐ │
│  │   App    │────▶│  Prometheus  │────▶│      Alertmanager           │ │
│  │ :3000    │metrics│  :9090     │alerts│      :9093                  │ │
│  └──────────┘     └──────────────┘     └───────────┬─────────────────┘ │
│                          │                          │                    │
│                     ┌────▼────┐              ┌──────▼────────┐         │
│                     │ Grafana │              │ Alert Webhook │         │
│                     │ :3002   │              │ :5001         │         │
│                     └─────────┘              └───────┬────────┘         │
│                                                      │                   │
│                    ┌─────────────────────────────────┼───────┐          │
│                    │                                 │       │          │
│              ┌─────▼─────┐                    ┌──────▼──┐  ┌─▼────────┐│
│              │  Email    │                    │ Telegram│  │  Twilio  ││
│              │  (SMTP)   │                    │   Bot   │  │   SMS    ││
│              └───────────┘                    └─────────┘  └──────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Prometheus (`infra/prometheus/`)

**Files:**
- `prometheus.yml` - Main scrape configuration
- `alerts.yml` - Alert rules (6 alerts)

**Scrape Targets:**
| Job | Target | Interval |
|-----|--------|----------|
| algo-trader | app:3000/metrics | 10s |
| prometheus | localhost:9090 | 30s |
| nginx | nginx-exporter:9113 | 15s |
| postgres | postgres-exporter:9187 | 30s |
| redis | redis-exporter:9121 | 15s |
| node | node-exporter:9100 | 15s |

**Alert Rules (6 total):**
| Alert | Severity | Condition | Duration |
|-------|----------|-----------|----------|
| CircuitBreakerOpen | critical | circuit_breaker_state == 1 | 1m |
| DailyLossLimit | warning | daily_pnl_usd < -500 | 5m |
| HighMemoryUsage | warning | memory > 0.8GB | 5m |
| ServiceDown | critical | up == 0 | 2m |
| HighErrorRate | warning | error rate > 5% | 5m |
| ExchangeLatencyHigh | warning | latency > 2s | 3m |

### 2. Grafana (`infra/grafana/`)

**Files:**
- `dashboards/trading-dashboard.json` - 8-panel trading dashboard
- `provisioning/dashboards.yml` - Dashboard provisioning
- `provisioning/datasources.yml` - Prometheus + Alertmanager datasources

**Dashboard Panels (8 total):**
| Panel | Type | Metric |
|-------|------|--------|
| Daily P&L (USD) | Stat | daily_pnl_usd |
| Win Rate (%) | Stat | win_rate_percent |
| Circuit Breaker | Stat | circuit_breaker_state |
| Open Positions | Stat | open_positions_total |
| Trades Executed | Time Series | trades_total |
| Memory Usage | Time Series | process_resident_memory_bytes |
| API Latency | Time Series | http_request_duration_seconds |
| Service Uptime | Time Series | process_start_time_seconds |

**Access:** http://localhost:3002 (admin/admin)

### 3. Alertmanager (`infra/alertmanager/`)

**Files:**
- `alertmanager.yml` - Alert routing configuration
- `alert-webhook-server.py` - Webhook for SMS/Telegram
- `Dockerfile.webhook` - Webhook container

**Notification Channels:**
| Channel | Config | Alerts |
|---------|--------|--------|
| Email | SMTP (SendGrid) | All alerts |
| Telegram | Bot API | Critical, CircuitBreaker, LossLimit |
| SMS (Twilio) | Twilio API | Critical, CircuitBreaker |

**Routing:**
- Default → Email only
- Critical severity → Email + Telegram + SMS
- CircuitBreakerOpen → Telegram + SMS (immediate)
- DailyLossLimit → Email + Telegram

### 4. Application Metrics (`src/middleware/prometheus-metrics.ts`)

**Custom Metrics:**
```typescript
// Counters
- trades_total (labels: symbol, exchange, side)
- signals_total (labels: symbol, signal_type)
- http_requests_total (labels: method, path, status)

// Gauges
- daily_pnl_usd (labels: strategy)
- win_rate_percent (labels: strategy)
- circuit_breaker_state (0=active, 1=halted)
- open_positions_total (labels: symbol, exchange)
- strategy_active (labels: strategy)

// Histograms
- exchange_api_latency_seconds (labels: exchange, operation)
- trade_execution_time_seconds (labels: exchange, symbol)
- http_request_duration_seconds (labels: method, path)
```

**Usage in code:**
```typescript
import { recordTrade, setCircuitBreakerState, setWinRate } from './middleware/prometheus-metrics';

// Record a trade
recordTrade('BTC/USDT', 'binance', 'buy', 125.50);

// Update circuit breaker
setCircuitBreakerState(true); // halted

// Update win rate
setWinRate(67.5);
```

## Quick Start

### Start the stack:
```bash
cd /Users/macbook/mekong-cli/apps/algo-trader
docker-compose up -d prometheus grafana alertmanager alert-webhook
```

### Access dashboards:
- Grafana: http://localhost:3002 (admin/admin)
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9094
- Alert Webhook: http://localhost:5001

### Configure notifications (optional):

Create `.env` file:
```bash
# Email (SendGrid)
SMTP_HOST=smtp.sendgrid.net:587
SMTP_FROM=alerts@your-domain.com
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-key
ALERT_EMAIL=your-email@example.com

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# Twilio SMS
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+0987654321
```

### Telegram Bot Setup:
1. Message @BotFather on Telegram
2. `/newbot` → name your bot
3. Copy the bot token to `TELEGRAM_BOT_TOKEN`
4. Add bot to your channel/group
5. Get chat ID: `curl "https://api.telegram.org/bot<token>/getUpdates"`
6. Set `TELEGRAM_CHAT_ID`

## Testing Alerts

### Trigger test alerts:
```bash
# Simulate high memory (in another terminal)
curl -X POST http://localhost:3000/admin/test/alert/memory

# Simulate circuit breaker
curl -X POST http://localhost:3000/admin/test/alert/circuit-breaker

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Alertmanager status
curl http://localhost:9094/api/v2/status
```

## Adding Custom Metrics

1. Edit `src/middleware/prometheus-metrics.ts`
2. Add metric definition:
```typescript
export const customMetric = new client.Gauge({
  name: 'custom_metric_name',
  help: 'Description of the metric',
  labelNames: ['label1', 'label2'] as const,
  registers: [register],
});
```
3. Export helper function:
```typescript
export function setCustomMetric(value: number): void {
  customMetric.set(value);
}
```
4. Use in your code:
```typescript
import { setCustomMetric } from './middleware/prometheus-metrics';
setCustomMetric(42);
```

## Troubleshooting

### Prometheus can't scrape app:
```bash
# Check app metrics endpoint
curl http://localhost:3000/metrics

# Should return Prometheus-format metrics
```

### Grafana shows no data:
1. Verify Prometheus datasource is connected
2. Check Prometheus targets: http://localhost:9090/targets
3. Ensure time range is correct (try "Last 15 minutes")

### Alerts not firing:
1. Check alert rules: http://localhost:9090/rules
2. Verify Alertmanager is receiving alerts: http://localhost:9094/api/v2/alerts
3. Check webhook logs: `docker logs algo-trader-alert-webhook`

### Webhook not sending SMS:
1. Verify Twilio credentials in `.env`
2. Check webhook logs: `docker logs algo-trader-alert-webhook`
3. Test Twilio connection:
```bash
docker exec algo-trader-alert-webhook python -c "from twilio.rest import Client; print('Twilio OK')"
```

## Production Deployment

For production deployment, add these to your deployment pipeline:

1. **Persist data volumes** - Backup `promdata`, `grafanadata`, `alertmanagerdata`
2. **Configure SSL** - Use reverse proxy (nginx/traefik) with Let's Encrypt
3. **Secure credentials** - Use Docker secrets or external secret manager
4. **Set up log aggregation** - Forward container logs to ELK/Loki
5. **Configure backup** - Regular backups of Grafana dashboards and Prometheus data

## References

- Prometheus docs: https://prometheus.io/docs/
- Grafana docs: https://grafana.com/docs/
- Alertmanager docs: https://prometheus.io/docs/alerting/alertmanager/
- Twilio docs: https://www.twilio.com/docs
- Telegram Bot API: https://core.telegram.org/bots/api
