# Resource Handling Refactor Plan

## Overview
Improve scalability from 5 to 10 concurrent resources by refactoring resource-handling logic across auth, config, db, jobs, and services modules.

## Current Analysis

### Rate Limiter (auth/rate_limiter.py)
- Uses token bucket algorithm with in-memory storage
- Default limits: 5-200 requests per minute depending on endpoint
- Thread-safe async operations
- Automatic cleanup of stale entries

### Database Connection (db/database.py)
- PostgreSQL connection pooling with asyncpg
- Current pool: min=2, max=10 connections
- Fallback to SQLite if DATABASE_URL not set

### Configuration (config/__init__.py)
- Simple logging configuration
- Needs more comprehensive resource configuration

### Jobs & Services
- Nightly reconciliation job (jobs/nightly_reconciliation.py)
- License enforcement service (services/license_enforcement.py)
- Need to analyze for resource efficiency

## Implementation Plan

### Phase 1: Auth Module Optimization
- Increase default rate limits by 2x for all presets
- Optimize token bucket algorithm for higher concurrency
- Add distributed rate limiting support (Redis backend option)

### Phase 2: Database Connection Pooling
- Increase connection pool size: min=5, max=20
- Add connection pool monitoring
- Optimize query execution with connection reuse

### Phase 3: Configuration Management
- Add resource configuration file (resources.toml)
- Support environment variable overrides for resource limits
- Add configuration validation

### Phase 4: Jobs & Services
- Optimize job scheduling for higher concurrency
- Add job queue management
- Improve service lifecycle management

### Phase 5: Testing & Validation
- Load testing with 10 concurrent resources
- Performance benchmarking
- Stress testing for failure scenarios

## Success Criteria
- Handle 10 concurrent resources without performance degradation
- Maintain response times under 100ms per request
- 99.9% availability under load
- All tests pass

## Risk Assessment
- High: Database connection exhaustion - mitigation: connection pool monitoring
- Medium: Rate limiter bottleneck - mitigation: distributed rate limiting
- Low: Configuration errors - mitigation: validation and defaults

## Next Steps
1. Start with Phase 1: Auth Module Optimization
2. Implement Phase 2: Database Connection Pooling
3. Develop Phase 3: Configuration Management
4. Optimize Phase 4: Jobs & Services
5. Run Phase 5: Testing & Validation
