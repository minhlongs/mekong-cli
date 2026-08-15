# Plugin Health Monitoring Operations Guide

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Production

This guide provides detailed operational procedures for managing the plugin health monitoring system in Mekong CLI.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Daily Operations](#daily-operations)
5. [Monitoring & Alerting](#monitoring--alerting)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)
8. [Configuration Reference](#configuration-reference)
9. [Recovery Procedures](#recovery-procedures)

---

## Overview

The Plugin Health Monitoring System provides comprehensive observability for all Mekong CLI plugins. It monitors:

- **Plugin Lifecycle**: Load/unload events, uptime, availability
- **Performance Metrics**: Command execution times, load durations
- **Error Tracking**: Failure rates, consecutive failures, error categories
- **Resource Usage**: Memory consumption (where available)
- **Auto-Recovery**: Automatic restart of failing plugins

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| PluginHealthMonitor | `src/core/plugin_health_monitor.py` | Core monitoring service |
| PluginHealthMetrics | `src/core/plugin_health_metrics.py` | OpenTelemetry metrics export |
| Health Endpoint | `src/core/health_endpoint.py` | HTTP health API |
| HealthReporter | `src/core/health_reporter.py` | Telemetry reporting to gateway |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Plugin System                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │   Plugin A  │  │   Plugin B  │  │      Plugin C       ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
│         │                │                   │             │
│         └────────────────┼───────────────────┘             │
│                          ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          PluginHealthMonitor (Singleton)            │  │
│  │  • Track plugin load/unload                         │  │
│  │  • Record command metrics                           │  │
│  │  • Periodic health checks                           │  │
│  │  • Auto-recovery coordination                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                 │
│         ┌────────────────┼────────────────┐               │
│         ▼                ▼                ▼               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  Metrics    │ │   Health    │ │   Events    │       │
│  │  Store      │ │  Endpoint   │ │   (bus)     │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                           │
│  ┌──────────────────────────────────────────────────────┐│
│  │          OpenTelemetry Export                       ││
│  │  • Prometheus metrics → OTel Collector → Prometheus││
│  │  • Grafana dashboards                              ││
│  │  • Alert rules                                     ││
│  └──────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Check Plugin Health Status

```bash
# Full system health (includes plugin status as component)
mekong health

# Dedicated plugin health endpoint (JSON)
curl http://localhost:9192/health/plugins | jq .

# Check specific plugin
mekong plugin health <plugin-name>

# View health history with timeline
mekong plugin health history --limit 20
```

### Manage Auto-Recovery

```bash
# Enable auto-recovery (default: enabled)
mekong plugin recovery enable

# Disable auto-recovery
mekong plugin recovery disable

# Check recovery status
mekong plugin recovery status

# Manually trigger recovery for a plugin
mekong plugin recovery trigger <plugin-name>
```

### Grafana Dashboard

1. Navigate to Grafana (usually `http://localhost:3000`)
2. Click "+" → "Import"
3. Upload `observability/dashboards/plugin-health.json`
4. Select Prometheus data source (default: `otel-collector:8889`)
5. Click "Import"

---

## Daily Operations

### Morning Checklist (5 minutes)

- [ ] Verify health endpoint responding: `curl http://localhost:9192/health`
- [ ] Check plugin health status in Grafana dashboard
- [ ] Review alert history for any overnight issues
- [ ] Check for plugins in UNHEALTHY state
- [ ] Verify auto-recovery is enabled (`mekong plugin recovery status`)

### Weekly Tasks (15 minutes)

- [ ] Review plugin health trends in Grafana
- [ ] Check for plugins with consistently high error rates
- [ ] Verify alert rules are firing correctly
- [ ] Review memory usage patterns
- [ ] Export plugin health history for backup
- [ ] Update plugins with known issues

---

## Monitoring & Alerting

### Health Endpoint

The health endpoint provides real-time plugin health status:

**Endpoint**: `GET /health/plugins`

**Response Example**:
```json
{
  "timestamp": "2026-06-20T20:45:00Z",
  "summary": {
    "total_plugins": 15,
    "healthy": 14,
    "degraded": 1,
    "unhealthy": 0,
    "errored": 0,
    "disabled": 0,
    "unknown": 0,
    "overall_status": "healthy"
  },
  "plugins": {
    "studio": {
      "status": "healthy",
      "load_time_ms": 234,
      "commands_executed": 1520,
      "commands_succeeded": 1518,
      "commands_failed": 2,
      "error_rate": 0.0013,
      "consecutive_failures": 0,
      "memory_usage_mb": 45.2
    }
  }
}
```

### Grafana Panels

The Plugin Health dashboard includes:

1. **Overall Plugin Health** - Summary stats (total, healthy, degraded, unhealthy)
2. **Health Status Timeline** - Trend of plugin health over time
3. **Command Execution Rate** - Total vs failed commands per second
4. **Error Rate Heatmap** - Error rate by plugin
5. **Load Times** - Bar gauge showing average load times
6. **Plugin Status Details** - Table with detailed status per plugin

### Alert Rules

Alert rules are defined in `observability/rules/plugin-health-rules.yml`.

#### Critical Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| `PluginMemoryCritical` | Memory >500MB for 1min | Immediate investigation, possible isolation breach |
| `PluginCriticalErrorRate` | Error rate >80% for 1min | Emergency response |
| `NoPluginsLoaded` | Zero plugins for 5min | System check, possible loader failure |

#### Warning Alerts

| Alert | Condition | Action |
|-------|-----------|--------|
| `PluginMemorySpike` | Memory >200MB for 2min | Investigate memory leak |
| `PluginHighErrorRate` | Error rate >50% for 3min | Check plugin logs, consider disabling |
| `PluginConsecutiveFailures` | >5 consecutive failures | Review error patterns |
| `PluginUsageSpike` | >1000 commands/min | Check for runaway agent |
| `ExcessivePluginCount` | >50 plugins loaded | Security investigation |

---

## Troubleshooting

### Issue: Plugin Shows as UNHEALTHY

**Diagnosis**:
```bash
# Get detailed plugin health
curl http://localhost:9192/health/plugins | jq '.plugins["<plugin-name">]'

# Check plugin logs
ls -la ~/.mekong/plugins/<plugin-name>/logs/

# Run manual health check
mekong plugin health check <plugin-name>

# Check recent command failures
mekong plugin health history --plugin <plugin-name> --limit 10
```

**Resolution**:
1. Review error message in health data
2. Check plugin-specific logs for stack traces
3. Test plugin manually: `mekong <plugin> <command>`
4. Attempt auto-recovery: `mekong plugin recovery trigger <plugin-name>`
5. If recovery fails, disable: `mekong plugin disable <plugin-name>`
6. Update or reinstall plugin if needed

---

### Issue: High Memory Usage

**Diagnosis**:
```bash
# Check Grafana for memory trends
# Look at mekong_plugin_memory_bytes metric

# Check plugin memory directly (if available)
curl http://localhost:9192/health/plugins | jq '.plugins[].memory_usage_mb'
```

**Resolution**:
1. Identify memory-heavy plugin from Grafana or endpoint
2. Check plugin code for memory leaks (large data structures, unbounded caches)
3. Restart CLI session to clear memory: `mekong shutdown && mekong`
4. Consider implementing memory limits for plugin
5. For persistent issues, disable or replace plugin

---

### Issue: High Error Rate

**Diagnosis**:
```bash
# Check error rate in Grafana heatmap
# View error rate over time

# Get failure details
mekong plugin health history --plugin <plugin-name> | grep -i error
```

**Resolution**:
1. Identify which commands are failing
2. Check plugin dependencies and configuration
3. Verify external service connectivity (APIs, databases)
4. Review recent code changes to plugin
5. Update plugin to latest version
6. If external service issue, consider temporary disable

---

### Issue: Auto-Recovery Not Working

**Diagnosis**:
```bash
# Check recovery status
mekong plugin recovery status

# Check plugin consecutive failures
curl http://localhost:9192/health/plugins | jq '.plugins[].consecutive_failures'

# View recovery attempt logs
tail -f ~/.mekong/logs/plugin-health.log | grep recovery
```

**Resolution**:
1. Verify auto-recovery is enabled: `mekong plugin recovery enable`
2. Check cooldown period hasn't been exceeded
3. Review recovery strategy configuration
4. Check plugin logs for recovery failure reasons
5. Manually trigger: `mekong plugin recovery trigger <plugin-name>`
6. Check registry.activate() method implementation

---

## Maintenance

### Configuration Backup

Backup plugin health configuration regularly:

```bash
# Backup health config
cp ~/.mekong/plugin_health.yaml ~/.mekong/backups/plugin_health.yaml.$(date +%Y%m%d)

# Backup health history
cp ~/.mekong/plugin_health.json ~/.mekong/backups/plugin_health.json.$(date +%Y%m%d)
```

### Log Rotation

Plugin health logs are stored in `~/.mekong/logs/`. Set up log rotation:

```bash
# Add to crontab
0 2 * * * find ~/.mekong/logs -name "*.log" -mtime +30 -delete
```

### Metric Retention

Metrics are retained in memory for `metrics_retention_minutes` (default: 1440 = 24 hours). Adjust in config:

```yaml
monitoring:
  metrics_retention_minutes: 2880  # 48 hours
```

---

## Configuration Reference

### Plugin Health Config (`~/.mekong/plugin_health.yaml`)

```yaml
# Monitoring configuration
monitoring:
  check_interval_seconds: 60       # Periodic health check interval
  metrics_retention_minutes: 1440  # How long to keep metrics in memory
  telemetry_enabled: true          # Send metrics to gateway
  health_endpoint_enabled: true    # Enable HTTP health endpoint
  health_endpoint_port: 9192       # Port for health endpoint

# Auto-recovery settings
auto_recovery:
  enabled: true                    # Enable auto-recovery globally
  max_attempts: 3                  # Max recovery attempts per incident
  cooldown_seconds: 300            # Cooldown between recovery attempts
  strategies:                      # Recovery strategies to try (order matters)
    - "graceful"  # Call on_unload() then activate()
    - "force"     # Direct activate without unload
    # - "reinstall"  # Future: pip uninstall/install

# Health thresholds
thresholds:
  error_rate_warning: 0.20         # 20% error rate = degraded
  error_rate_critical: 0.50       # 50% error rate = unhealthy
  consecutive_failures_warning: 3  # 3 consecutive failures = degraded
  consecutive_failures_critical: 5 # 5 consecutive failures = unhealthy
  load_time_ms_warning: 5000       # 5s load time = degraded
  load_time_ms_critical: 10000    # 10s load time = degraded

# Isolation breach thresholds
isolation:
  max_memory_mb: 500              # Alert if plugin exceeds this
  max_processes: 1                # Max processes per plugin
  max_network_connections_per_min: 100
```

### Environment Variables

```bash
# Override health endpoint port
export MEKONG_HEALTH_PORT=9192

# Disable health monitoring (emergency)
export MEKONG_PLUGIN_HEALTH_ENABLED=false

# Override check interval
export MEKONG_PLUGIN_HEALTH_INTERVAL=30

# Disable auto-recovery
export MEKONG_PLUGIN_RECOVERY_ENABLED=false
```

---

## Recovery Procedures

### Standard Recovery Flow

When a plugin becomes UNHEALTHY:

1. **Detection**: PluginHealthMonitor detects unhealthy status
2. **Evaluation**: Check if cooldown period is active
3. **Recovery Attempt**: Try strategies in order (graceful, force)
4. **Verification**: Re-check plugin health after recovery
5. **Escalation**: If all strategies fail, mark for manual intervention

### Manual Recovery

```bash
# Check plugin status
mekong plugin health <plugin-name>

# Manually trigger recovery
mekong plugin recovery trigger <plugin-name>

# If recovery fails, disable plugin
mekong plugin disable <plugin-name>

# Investigate logs
tail -f ~/.mekong/plugins/<plugin-name>/logs/*.log

# After fixing, re-enable
mekong plugin enable <plugin-name>
```

### Emergency Disable

If a plugin is causing system instability:

```bash
# Immediate disable (bypasses normal flow)
mekong plugin disable <plugin-name> --force

# Verify it's disabled
mekong plugin health | grep <plugin-name>

# If CLI becomes unusable, edit config:
# ~/.mekong/plugin_health.yaml → set plugin to disabled: true
# Or remove plugin from ~/.mekong/plugins/ and restart
```

### Recovery After Fix

1. Update plugin code or configuration
2. Reinstall plugin if necessary
3. Re-enable: `mekong plugin enable <plugin-name>`
4. Verify health: `mekong plugin health <plugin-name>`
5. Monitor for 15 minutes to ensure stability

---

## Metrics Reference

### Prometheus Metrics Exported

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `mekong_plugin_commands_total` | counter | `plugin`, `command`, `status` | Total plugin command executions |
| `mekong_plugin_command_duration_seconds` | histogram | `plugin`, `command` | Command execution duration |
| `mekong_plugin_loads_total` | counter | `plugin`, `status` | Plugin load attempts |
| `mekong_plugin_load_duration_seconds` | histogram | `plugin` | Plugin load duration |
| `mekong_plugin_health_status` | gauge | `plugin`, `status` | Current health status (1-5) |
| `mekong_plugin_recovery_attempts_total` | counter | `plugin` | Recovery attempts |
| `mekong_plugin_recovery_success_total` | counter | `plugin` | Successful recoveries |
| `mekong_plugin_recovery_failure_total` | counter | `plugin` | Failed recoveries |
| `mekong_plugins_loaded` | gauge | - | Total loaded plugins |
| `mekong_plugins_healthy` | gauge | - | Count of healthy plugins |
| `mekong_plugins_degraded` | gauge | - | Count of degraded plugins |
| `mekong_plugins_unhealthy` | gauge | - | Count of unhealthy plugins |

### Health Status Codes

| Status | Code | Meaning | Action |
|--------|------|---------|--------|
| healthy | 1 | Operating normally | No action |
| degraded | 2 | Some issues but functional | Monitor, investigate |
| unhealthy | 3 | Not functioning correctly | Recovery triggered |
| error | 4 | In error state | Manual intervention |
| disabled | 5 | Manually disabled | No action until enabled |
| unknown | 0 | No health data | Check plugin status |

---

## Support

For issues not covered in this guide:

1. Check plugin-specific documentation
2. Review system logs: `~/.mekong/logs/`
3. Consult the main operator runbook: `docs/operator-runbook.md`
4. Search GitHub issues: `https://github.com/mekong-cli/mekong-cli/issues`

---

**Document Version**: 1.0.0
**Last Updated**: 2026-06-20
**Next Review**: 2026-09-20
