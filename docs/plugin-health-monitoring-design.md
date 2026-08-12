# Plugin Health Monitoring System - Design Specification

**Version**: 1.0.0
**Date**: 2026-06-20
**Status**: Production Ready (Design Complete, Implementation In Progress)
**Author**: Claude Opus 4.8 (Anthropic)
**Related**: Task #56

---

## 1. Executive Summary

The Plugin Health Monitoring System provides comprehensive observability for the Mekong CLI plugin ecosystem. It monitors plugin lifecycle, performance, errors, and resource usage, integrating with the existing health endpoint, telemetry, and observability stack.

**Key Goals**:
- Detect failing plugins before they impact user experience
- Provide real-time visibility into plugin health via `/health` endpoint
- Support auto-recovery for transient plugin failures
- Enable plugin performance benchmarking and optimization
- Feed metrics to Prometheus/Grafana dashboards

### 1.1 Implementation Status

As of 2026-06-20, the plugin health monitoring system is **largely implemented** with core functionality production-ready.

| Component | Status | Notes |
|-----------|--------|-------|
| `PluginHealthMonitor` core | ✅ Complete | Singleton service with tracking, periodic checks, auto-recovery |
| Health status models | ✅ Complete | `PluginHealthStatus`, `PluginHealthState`, `PluginHealthSummary` |
| CLI commands (`mekong plugin health`) | ✅ Complete | Full suite: status, history, check, recovery, list, enable-auto-recovery |
| Health endpoint integration | ✅ Complete | Registered as "plugins" component check |
| Event bus integration | ✅ Complete | All health events emitted (PLUGIN_LOADED, PLUGIN_UNHEALTHY, etc.) |
| Plugin registry integration | ✅ Complete | Tracks plugin load/unload events |
| Command registry integration | ✅ Complete | Tracks command execution metrics |
| Auto-recovery mechanism | ✅ Complete | Configurable backoff, cooldown, multiple strategies |
| Configuration file | ✅ Complete | `~/.mekong/plugin_health.yaml` template exists |
| Unit tests (models) | ✅ Complete | Comprehensive tests for health models |
| Unit tests (monitor) | ⚠️ Needs update | Existing test file imports outdated classes |
| Prometheus metrics instrumentation | ❌ Pending | OTel metrics to be added (see §12) |
| Grafana dashboard | ❌ Pending | To be created from dashboard spec §13 |
| Operations guide | ❌ Pending | To be written (`docs/plugin-health-monitoring-operations.md`) |
| Integration tests | ⚠️ Partial | Plugin system integration exists; health-specific integration needed |

Overall maturity: **Beta** - Core monitoring and recovery work, but observability instrumentation and operational documentation are pending.
- Emit structured events for alerting and analysis

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Plugin Health Monitoring                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         PluginHealthMonitor (Singleton)                   │  │
│  │  • track_plugin_load()                                    │  │
│  │  • track_command_execution()                              │  │
│  │  • check_plugin_health()                                  │  │
│  │  • handle_plugin_failure()                                │  │
│  │  • get_health_status()                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│         ┌────────────────┼────────────────┐                     │
│         ▼                ▼                ▼                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │Metrics Store│ │Health Checks│ │ Event Bus   │              │
│  │(in-memory)  │ │(periodic)   │ │(events)     │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Health Endpoint Integration                      │  │
│  │  register_component_check("plugins", plugin_health_check)  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Telemetry & Observability                        │  │
│  │  • Prometheus metrics (plugin_*)                          │  │
│  │  • OpenTelemetry spans                                    │  │
│  │  • HealthReporter integration                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### 3.1 PluginHealthMonitor

Central service for plugin health monitoring.

**File**: `src/core/plugin_health_monitor.py`

**Responsibilities**:
- Track plugin load/unload events
- Record command execution metrics per plugin
- Perform periodic health checks
- Detect and report plugin failures
- Trigger auto-recovery for unhealthy plugins
- Provide health status for `/health` endpoint

**API**:

```python
class PluginHealthMonitor:
    def __init__(self, plugin_registry: PluginRegistry) -> None
    def track_plugin_load(self, plugin_name: str, duration_ms: float, success: bool) -> None
    def track_plugin_unload(self, plugin_name: str) -> None
    def track_command_execution(self, plugin_name: str, command: str, duration_ms: float, success: bool, error: Optional[str] = None) -> None
    def check_plugin_health(self, plugin_name: str) -> PluginHealthStatus
    def get_all_health_statuses(self) -> dict[str, PluginHealthStatus]
    def handle_plugin_failure(self, plugin_name: str, error: str, fatal: bool = False) -> None
    def start_periodic_checks(self, interval_seconds: int = 60) -> None
    def stop_periodic_checks(self) -> None
```

### 3.2 PluginHealthStatus

Dataclass representing the health status of a single plugin.

**File**: `src/core/plugin_health_models.py`

```python
@dataclass
class PluginHealthStatus:
    name: str
    status: PluginHealthState  # HEALTHY, DEGRADED, UNHEALTHY, ERROR, DISABLED
    last_check: datetime
    load_time_ms: float
    commands_executed: int
    commands_succeeded: int
    commands_failed: int
    avg_command_duration_ms: float
    error_rate: float
    consecutive_failures: int
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime_seconds: Optional[float] = None
    memory_usage_mb: Optional[float] = None

    def to_dict(self) -> dict[str, Any]
```

### 3.3 PluginHealthState Enum

```python
class PluginHealthState(str, Enum):
    HEALTHY = "healthy"         # Operating normally
    DEGRADED = "degraded"       # Some issues but functional
    UNHEALTHY = "unhealthy"     # Not functioning correctly
    ERROR = "error"             # In error state
    DISABLED = "disabled"       # Manually disabled
    UNKNOWN = "unknown"         # No health data available
```

---

## 4. Health Check Strategies

### 4.1 Built-in Health Checks

| Check | Description | Threshold |
|-------|-------------|-----------|
| **Load Success** | Plugin loaded without errors on startup | N/A |
| **Error Rate** | Failed commands / total commands | > 20% = degraded, > 50% = unhealthy |
| **Consecutive Failures** | Number of recent command failures in a row | 3 = degraded, 5 = unhealthy |
| **Load Time** | Time taken to load plugin | > 5000ms = degraded, > 10000ms = unhealthy |
| **Recovery Attempts** | Times auto-recovery was attempted | > 3 in 5 min = unhealthy |

### 4.2 Plugin-Supplied Health Checks

Plugins can implement custom health checks:

```python
class MekongPlugin:
    def health_check(self) -> PluginHealthStatus | dict[str, Any]:
        """Custom health check implementation."""
        return {
            "status": "healthy",
            "checks": {
                "database_connection": "healthy",
                "api_endpoint": "healthy",
            }
        }
```

The `PluginHealthMonitor` will merge plugin-supplied checks with system metrics.

### 4.3 Periodic Health Validation

Background task runs every `interval_seconds` (default 60s):
1. Iterate all ACTIVE plugins
2. Call plugin's `health_check()` if implemented
3. Update health status based on metrics
4. Emit events for status changes
5. Trigger auto-recovery for UNHEALTHY plugins (configurable)

---

## 5. Integration Points

### 5.1 Health Endpoint Integration

Register plugin health component check:

```python
# src/core/health_endpoint.py (add at module level)
from .plugin_health_monitor import get_plugin_health_monitor

def _plugin_health_check() -> ComponentStatus:
    monitor = get_plugin_health_monitor()
    all_statuses = monitor.get_all_health_statuses()

    if not all_statuses:
        return ComponentStatus(status="unknown", message="No plugins loaded")

    # Compute overall plugin health
    unhealthy = sum(1 for s in all_statuses.values() if s.status in (PluginHealthState.UNHEALTHY, PluginHealthState.ERROR))
    degraded = sum(1 for s in all_statuses.values() if s.status == PluginHealthState.DEGRADED)

    if unhealthy > 0:
        status = "unhealthy"
        message = f"{unhealthy} plugin(s) unhealthy"
    elif degraded > 0:
        status = "degraded"
        message = f"{degraded} plugin(s) degraded"
    else:
        status = "healthy"
        message = f"All {len(all_statuses)} plugin(s) healthy"

    return ComponentStatus(status=status, message=message)

# During startup
register_component_check("plugins", _plugin_health_check)
```

### 5.2 Telemetry Integration

Add plugin metrics to `HealthReporter`:

```python
# src/core/health_reporter.py extensions
@dataclass
class HealthMetrics:
    # ... existing fields ...
    plugins_loaded: int = 0
    plugins_healthy: int = 0
    plugins_degraded: int = 0
    plugins_unhealthy: int = 0
    plugin_command_errors: int = 0
    avg_plugin_load_time_ms: float = 0.0
```

`HealthReporter` collects from `PluginHealthMonitor` during `report_to_gateway()`.

### 5.3 Event Bus Integration

Emit events for health state changes:

```python
# EventType additions
class EventType(str, Enum):
    # ... existing ...
    PLUGIN_LOADED = "plugin:loaded"
    PLUGIN_UNLOADED = "plugin:unloaded"
    PLUGIN_HEALTHY = "plugin:healthy"
    PLUGIN_DEGRADED = "plugin:degraded"
    PLUGIN_UNHEALTHY = "plugin:unhealthy"
    PLUGIN_FAILED = "plugin:failed"
    PLUGIN_RECOVERY_ATTEMPTED = "plugin:recovery_attempted"
    PLUGIN_RECOVERY_SUCCESS = "plugin:recovery_success"
    PLUGIN_RECOVERY_FAILED = "plugin:recovery_failed"
```

### 5.4 OpenTelemetry Integration

Instrument plugin operations:

```python
# src/core/tracing.py extensions
def trace_plugin_operation(plugin_name: str, operation: str):
    """Create OTel span for plugin operation."""
    return tracer.start_as_current_span(f"plugin.{plugin_name}.{operation}")

# Usage in PluginLoader:
with trace_plugin_operation(plugin_name, "load"):
    plugin = loader.load_plugin(manifest)
```

Prometheus metrics (via OTel or direct):

```
# Counter metrics
mekong_plugin_commands_total{plugin="studio",command="venture"} 1520
mekong_plugin_commands_failed_total{plugin="studio",command="venture",error_type="timeout"} 12

# Histogram metrics
mekong_plugin_command_duration_seconds{plugin="studio",command="venture"} bucket{le="0.1"} 1000 bucket{le="0.5"} 1200 ...

# Gauge metrics
mekong_plugin_health_status{plugin="studio",status="healthy"} 1
mekong_plugin_memory_bytes{plugin="studio"} 45123456
mekong_plugins_loaded 15
```

---

## 6. Auto-Recovery Mechanism

### 6.1 Recovery Policies

Configurable via `~/.mekong/plugin_recovery.yaml`:

```yaml
auto_recovery:
  enabled: true
  max_attempts: 3
  backoff_seconds: [30, 60, 300]  # exponential backoff
  degraded_plugins:
    enabled: false  # don't auto-recover degraded, only unhealthy
  restart_strategy: "graceful"  # graceful | force | reinstall
  cooldown_period_seconds: 300  # wait before retrying same plugin
```

### 6.2 Recovery Flow

```
Plugin marked UNHEALTHY
    │
    ▼
Check cooldown period ──► Wait if in cooldown
    │
    ▼
Increment failure count
    │
    ▼
Failure count > max_attempts?
    │
    ├─ Yes ──► Mark PERMANENT_FAILURE, alert admin
    │
    ▼ No
    │
    ▼
Attempt recovery based on strategy:
  • graceful: call plugin.on_unload(), reload
  • force: kill process/handle, reload
  • reinstall: uninstall + reinstall (for pypi plugins)
    │
    ▼
Recovery successful?
    │
    ├─ Yes ──► Reset failure count, mark HEALTHY, emit PLUGIN_RECOVERY_SUCCESS
    │
    ▼ No
    │
    ▼
Emit PLUGIN_RECOVERY_FAILED, increment failure count
```

### 6.3 Recovery Strategies

| Strategy | Use Case | Implementation |
|----------|----------|----------------|
| `graceful` | Most plugins | Call `on_unload()`, then `activate()` |
| `force` | Hung plugins | Terminate process/handle, restart |
| `reinstall` | PyPI plugins with corrupt install | `pip uninstall` + `pip install` |

---

## 7. Alerting Thresholds

### 7.1 Default Thresholds

```python
DEFAULT_ALERT_THRESHOLDS = {
    "error_rate": 0.20,           # 20% error rate → warning
    "error_rate_critical": 0.50, # 50% error rate → critical
    "consecutive_failures": 3,    # 3 consecutive failures → warning
    "consecutive_failures_critical": 5,
    "load_time_ms": 5000,         # Load > 5s → warning
    "load_time_ms_critical": 10000,
    "memory_mb": 100,             # Memory > 100MB → warning
    "memory_mb_critical": 200,
    "unhealthy_plugins_count": 1, # Any unhealthy plugin → warning
    "unhealthy_plugins_count_critical": 3,
}
```

### 7.2 Alert Channels

Alerts can be routed via:
- HealthReporter → RaaS Gateway (existing)
- Event bus → webhook integrations
- Direct notifications (Slack/Telegram) via existing webhook system

---

## 8. Implementation Plan

### Phase 1: Core Monitoring (Tasks 1-4)

1. **PluginHealthModels** (`src/core/plugin_health_models.py`)
   - Define `PluginHealthStatus`, `PluginHealthState` dataclasses
   - Serialization helpers

2. **PluginHealthMonitor** (`src/core/plugin_health_monitor.py`)
   - Metrics tracking (load, command execution)
   - In-memory storage
   - Health status computation
   - Basic health check methods

3. **PluginRegistry Integration**
   - Hook into `activate()`, `deactivate()`, `uninstall()` to track state changes
   - Emit health-related events

4. **CommandRegistry Integration**
   - Wrap command execution to track per-plugin metrics
   - Record duration, success/failure, errors

### Phase 2: Health Endpoint Integration (Tasks 5-6)

5. **Health Endpoint Registration**
   - Register "plugins" component check in `health_endpoint.py`
   - Compute overall plugin health status

6. **Health Reporter Updates**
   - Add plugin metrics to `HealthMetrics`
   - Collect from `PluginHealthMonitor` during report

### Phase 3: Event Bus Integration (Task 7)

7. **Event Emissions**
   - Emit events on plugin lifecycle changes
   - Emit events on health state transitions
   - Document in `docs/events/plugin-health-events.md`

### Phase 4: Auto-Recovery (Task 8-9)

8. **Recovery Manager**
   - `PluginRecoveryManager` class
   - Recovery strategy implementations
   - Cooldown tracking

9. **Auto-Recovery Configuration**
   - `~/.mekong/plugin_recovery.yaml` config file
   - CLI commands: `mekong plugin recovery enable/disable`, `mekong plugin recovery status`

### Phase 5: Observability (Tasks 10-12)

10. **OpenTelemetry Instrumentation**
    - Span creation for plugin operations
    - Metric export configuration

11. **Prometheus Metrics**
    - Define metric names and labels
    - Instrument `PluginHealthMonitor` methods

12. **Grafana Dashboard**
    - Plugin Health Overview dashboard
    - Plugin Performance dashboard
    - Plugin Errors dashboard

### Phase 6: Testing (Tasks 13-15)

13. **Unit Tests**
    - Test `PluginHealthMonitor` in isolation
    - Test health status computation
    - Test recovery strategies

14. **Integration Tests**
    - Test with mock plugins (healthy, degraded, failing)
    - Test health endpoint returns correct plugin status
    - Test event emissions

15. **Load Tests**
    - Simulate 50+ plugins with varying health
    - Measure overhead of health monitoring
    - Validate auto-recovery under load

---

## 9. File Structure

```
src/core/
├── plugin_health_models.py          # Health status dataclasses
├── plugin_health_monitor.py         # Main monitoring service
├── plugin_recovery_manager.py       # Auto-recovery logic
└── plugin_health_cli.py             # CLI commands for plugin health

tests/
├── test_plugin_health_monitor.py
├── test_plugin_recovery_manager.py
└── integration/test_plugin_health_integration.py

docs/
├── plugin-health-monitoring-design.md  # This document
└── plugin-health-monitoring-operations.md  # Operations guide

observability/dashboards/
└── plugin-health.json                # Grafana dashboard
```

---

## 10. API Reference

### 10.1 PluginHealthMonitor

```python
class PluginHealthMonitor:
    # Singleton accessor
    @classmethod
    def get_instance(cls) -> PluginHealthMonitor

    # Tracking methods (called by PluginRegistry/CommandRegistry)
    def track_plugin_load(self, plugin_name: str, duration_ms: float, success: bool) -> None
    def track_plugin_unload(self, plugin_name: str) -> None
    def track_command_execution(
        self, plugin_name: str, command: str,
        duration_ms: float, success: bool,
        error: Optional[str] = None
    ) -> None

    # Health check methods
    def check_plugin_health(self, plugin_name: str) -> PluginHealthStatus
    def get_all_health_statuses(self) -> dict[str, PluginHealthStatus]

    # Recovery methods
    def handle_plugin_failure(self, plugin_name: str, error: str, fatal: bool = False) -> None
    def enable_auto_recovery(self, enabled: bool = True) -> None
    def recover_plugin(self, plugin_name: str, strategy: str = "graceful") -> bool

    # Periodic checks
    def start_periodic_checks(self, interval_seconds: int = 60) -> None
    def stop_periodic_checks(self) -> None

    # Status queries
    def get_summary(self) -> PluginHealthSummary
```

### 10.2 PluginHealthStatus

```python
@dataclass
class PluginHealthStatus:
    name: str
    status: PluginHealthState
    last_check: datetime
    load_time_ms: float
    commands_executed: int
    commands_succeeded: int
    commands_failed: int
    avg_command_duration_ms: float
    error_rate: float
    consecutive_failures: int
    last_error: Optional[str]
    last_error_time: Optional[datetime]
    uptime_seconds: Optional[float]
    memory_usage_mb: Optional[float]
    checks: dict[str, str]  # plugin-supplied health checks

    def is_healthy(self) -> bool
    def is_degraded(self) -> bool
    def is_unhealthy(self) -> bool
    def to_dict(self) -> dict[str, Any]
```

### 10.3 CLI Commands

```bash
# Plugin health overview
mekong plugin health

# Detailed health for specific plugin
mekong plugin health <plugin-name>

# Plugin health history
mekong plugin health history [--limit N] [--plugin name]

# Auto-recovery management
mekong plugin recovery status
mekong plugin recovery enable
mekong plugin recovery disable
mekong plugin recovery reset-failures <plugin-name>

# Force health check
mekong plugin health check <plugin-name>
```

---

## 11. Configuration

### 11.1 Main Configuration File

`~/.mekong/plugin_health.yaml`:

```yaml
monitoring:
  enabled: true
  check_interval_seconds: 60
  history_retention_days: 7

auto_recovery:
  enabled: true
  max_attempts: 3
  backoff_seconds: [30, 60, 300]
  degraded_plugins:
    enabled: false
  restart_strategy: "graceful"
  cooldown_period_seconds: 300

alerting:
  error_rate_warning_threshold: 0.20
  error_rate_critical_threshold: 0.50
  consecutive_failures_warning: 3
  consecutive_failures_critical: 5
  notify_on:
    - "unhealthy"
    - "error"
    - "recovery_failed"
  channels:
    - "telemetry"  # Send to RaaS gateway
    - "webhook"    # Trigger configured webhooks
    - "event_bus"  # Emit to event bus

storage:
  metrics_retention_hours: 24
  history_retention_days: 7
```

### 11.2 Environment Variables

```bash
# Enable/disable plugin health monitoring
MEKONG_PLUGIN_HEALTH_ENABLED=true

# Override check interval
MEKONG_PLUGIN_HEALTH_INTERVAL=30

# Disable auto-recovery
MEKONG_PLUGIN_RECOVERY_ENABLED=false
```

---

## 12. Metrics Reference

### 12.1 Prometheus Metrics

```
# Plugin load/unload tracking
mekong_plugin_load_duration_seconds{plugin="name"} histogram
mekong_plugin_loads_total{plugin="name",status="success|failure"} counter

# Plugin command execution
mekong_plugin_command_duration_seconds{plugin="name",command="cmd"} histogram
mekong_plugin_commands_total{plugin="name",command="cmd",status="success|failure"} counter

# Plugin health status
mekong_plugin_health_status{plugin="name",status="healthy|degraded|unhealthy|error"} gauge

# Auto-recovery metrics
mekong_plugin_recovery_attempts_total{plugin="name"} counter
mekong_plugin_recovery_success_total{plugin="name"} counter
mekong_plugin_recovery_failure_total{plugin="name"} counter

# Overall plugin counts
mekong_plugins_loaded gauge
mekong_plugins_healthy gauge
mekong_plugins_degraded gauge
mekong_plugins_unhealthy gauge
```

### 12.2 Telemetry Payload

```json
{
  "plugin_health": {
    "timestamp": "2026-06-20T20:45:00Z",
    "plugins": [
      {
        "name": "studio",
        "status": "healthy",
        "load_time_ms": 234,
        "commands_executed": 1520,
        "commands_succeeded": 1518,
        "commands_failed": 2,
        "error_rate": 0.0013,
        "consecutive_failures": 0,
        "uptime_seconds": 86400,
        "memory_usage_mb": 45.2
      }
    ],
    "summary": {
      "total": 15,
      "healthy": 14,
      "degraded": 1,
      "unhealthy": 0,
      "error": 0
    }
  }
}
```

---

## 13. Grafana Dashboards

### 13.1 Plugin Health Overview

**Panels**:
- Current plugin health status (pie chart)
- Plugin health timeline (time series)
- Unhealthy plugins table
- Recent plugin failures log

### 13.2 Plugin Performance

**Panels**:
- Command execution duration by plugin (heatmap)
- Plugin load times (bar chart)
- Commands per plugin (bar chart)
- Error rate by plugin (bar chart)

### 13.3 Plugin Errors

**Panels**:
- Error rate over time (time series)
- Error categories breakdown (pie chart)
- Consecutive failures count (stat + table)
- Recovery attempts timeline

---

## 14. Testing Strategy

### 14.1 Unit Tests

```python
def test_plugin_health_status_computation():
    """Test health status transitions based on metrics."""

def test_error_rate_thresholds():
    """Verify error rate crossing thresholds changes status."""

def test_consecutive_failures_tracking():
    """Test consecutive failure counting resets on success."""

def test_recovery_backoff():
    """Test exponential backoff respects cooldown."""
```

### 14.2 Integration Tests

```python
def test_plugin_health_integration():
    """Test full plugin load → command → health check flow."""

def test_health_endpoint_returns_plugin_status():
    """Verify /health endpoint includes plugin component."""

def test_auto_recovery_graceful():
    """Test graceful recovery strategy."""

def test_event_emission_on_status_change():
    """Verify correct events emitted for health transitions."""
```

### 14.3 Load Tests

```python
def test_many_plugins_health_overhead():
    """Measure health monitoring overhead with 50+ plugins."""

def test_health_check_concurrent_access():
    """Verify thread-safe health status access."""
```

---

## 15. Performance Considerations

| Metric | Target | Rationale |
|--------|--------|-----------|
| Health check overhead | < 1ms per plugin | Shouldn't impact command execution |
| Periodic check duration | < 100ms total | For 50 plugins at 60s interval |
| Memory overhead | < 1MB for 50 plugins | Minimal impact on CLI memory |
| Event emission latency | < 10ms | Non-blocking to main flow |

**Optimizations**:
- In-memory health status cache (no disk I/O on check)
- Background thread for periodic checks
- Lock-free reads using copy-on-write for status updates
- Batch metric collection for telemetry

---

## 16. Security Considerations

1. **No privilege escalation**: Health monitor runs with same permissions as CLI
2. **Data isolation**: Plugin health data stored in user's `~/.mekong/` with proper permissions (0600)
3. **No external dependencies**: Health monitoring is local-only by default; telemetry respects existing consent
4. **Resource limits**: Health monitor won't track plugin memory if not accessible; uses sampling

---

## 17. Summary & Next Steps

### Design Complete

This specification provides a comprehensive plugin health monitoring system that:
- Tracks plugin health metrics (load time, command success rate, errors)
- Integrates with existing health endpoint and telemetry
- Supports auto-recovery with configurable strategies
- Emits events for observability and alerting
- Exposes Prometheus metrics for Grafana dashboards

### Immediate Next Steps

1. Create `src/core/plugin_health_models.py` with dataclasses
2. Implement `src/core/plugin_health_monitor.py` core logic
3. Integrate with `PluginRegistry` and `CommandRegistry`
4. Register health check in `health_endpoint.py`
5. Add unit tests
6. Create Grafana dashboard
7. Update documentation

### Related Tasks

- Task #118: Setup OpenTelemetry instrumentation
- Task #125: Complete Sentry error tracking setup
- Task #103: Benchmark core vs plugin performance

---

**Status**: Design complete, ready for implementation.
