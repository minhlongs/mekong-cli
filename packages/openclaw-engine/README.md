# @mekong/openclaw-engine

Mission orchestration engine for AI-operated business platforms. TypeScript SDK with complexity classification, circuit breaker, and AGI scoring.

## Install

```bash
npm install @mekong/openclaw-engine
```

## Quick Start

```typescript
import { OpenClawEngine } from '@mekong/openclaw-engine';

const engine = new OpenClawEngine({
  enableCircuitBreaker: true,
  enableLearning: true,
});

// Classify mission complexity
const complexity = engine.classifyComplexity('Build a REST API with auth');
// => 'standard'

// Submit a mission
const result = await engine.submitMission({
  goal: 'Build a REST API with auth',
  complexity,
});
console.log(result.id, result.status, result.creditsUsed);

// Check engine health
const health = engine.getHealth();
console.log(health.agiScore, health.circuitBreakerState);

// Clean up
engine.destroy();
```

## API

### `OpenClawEngine`

| Method | Returns | Description |
|--------|---------|-------------|
| `classifyComplexity(goal)` | `trivial \| standard \| complex \| epic` | Heuristic complexity from goal text |
| `submitMission(config)` | `MissionResult` | Execute mission with circuit breaker |
| `getHealth()` | `EngineHealth` | Uptime, AGI score, circuit state |
| `modules` | `EngineModules` | Lazy-loaded sub-modules (RaaS, etc.) |
| `destroy()` | `void` | Clean up timers |

### Credit Costs

| Complexity | Credits (MCU) |
|-----------|---------------|
| trivial | 1 |
| standard | 3 |
| complex | 10 |
| epic | 25 |

### Circuit Breaker

Auto-opens when failure rate > 50% over 5+ missions. Transitions to `half-open` after 30s cooldown. Rejects missions while `open`.

## Sub-modules

Access via `engine.modules`:

- **RaaS** — credit management, tenant operations
- **Orchestration** — mission dispatch, queue management
- **Intelligence** — learning, pattern recognition
- **Reliability** — retry, fallback, health checks
- **Safety** — input validation, output sanitization
- **Observability** — metrics, logging, tracing

## License

MIT
