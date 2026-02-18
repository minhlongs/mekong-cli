```markdown
# AgencyOS Tasks: Real-Time Ignition System

> Mission: REALTIME_IGNITION — Enabling instant task activation and synchronization across distributed agents.

## Overview

The `tasks` module within AgencyOS implements the **Real-Time Ignition System**, a high-performance, low-latency engine designed to trigger, coordinate, and synchronize task execution across autonomous agent networks in real time. Built for mission-critical responsiveness, this system ensures that task activation events are propagated with sub-millisecond precision, enabling dynamic, event-driven workflows.

## Core Features

- **Instant Task Ignition**: Trigger tasks immediately upon event receipt, bypassing traditional polling or queue delays.
- **Distributed Synchronization**: Coordinate ignition events across multiple agent nodes with consensus-aware timing.
- **Priority-Based Queuing**: Dynamically prioritize ignition requests based on mission-criticality and agent capacity.
- **Failover Resilience**: Auto-reignite failed tasks with exponential backoff and agent health validation.
- **Audit Trail**: Full logging of ignition events, timestamps, and agent acknowledgments (see `mission_REALTIME_IGNITION.txt`).

## Architecture

```
Event Source → Ignition Router → Agent Registry → Task Executor → Acknowledgment Loop
                     │
                     └── Audit Logger → Persistent Log (mission_REALTIME_IGNITION.txt)
```

The system leverages a publish-subscribe model with zero-copy message passing for maximum throughput. Agents register their ignition capabilities and listen for tagged events. Upon receipt, the router validates context, assigns priority, and dispatches to the nearest capable executor.

## Usage

```bash
# Start the ignition service
npm start

# Trigger a task manually (for testing)
curl -X POST http://localhost:3000/ignite \
  -H "Content-Type: application/json" \
  -d '{"taskID": "TASK-771", "agentID": "AGENT-OMEGA", "priority": "CRITICAL"}'
```

## Configuration

All runtime settings are managed via environment variables:

| Variable | Description |
|----------|-------------|
| `IGNITION_PORT` | Port for the ignition API (default: 3000) |
| `IGNITION_TIMEOUT` | Max wait for agent acknowledgment (ms, default: 500) |
| `LOG_FILE` | Path to mission log (default: `mission_REALTIME_IGNITION.txt`) |
| `MAX_CONCURRENT_TASKS` | Max parallel ignitions per agent (default: 10) |

## Mission Log

All ignition events are permanently recorded in `mission_REALTIME_IGNITION.txt`, formatted as:

```
[YYYY-MM-DDTHH:mm:ss.SSSZ] AGENT-ID: TASK-ID → STATUS [PRIORITY]
```

Example:
```
[2024-06-15T08:23:45.123Z] AGENT-OMEGA: TASK-771 → IGNITED [CRITICAL]
[2024-06-15T08:23:45.187Z] AGENT-OMEGA: TASK-771 → ACKNOWLEDGED [CRITICAL]
```

## Dependencies

- Node.js 18+
- Express.js (for API layer)
- Redis (for distributed state coordination)
- Winston (for logging)

## License

AgencyOS — Proprietary. For internal use by authorized AgencyOS agents only.

© 2024 AgencyOS. All rights reserved.
```