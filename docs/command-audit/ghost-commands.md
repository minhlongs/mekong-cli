# Ghost Commands — Python Module Exists, No Markdown Spec

> Audit date: 2026-04-17
> Definition: `src/commands/*.py` exists but no corresponding `.claude/commands/**/*.md`.
> These are implementation-only modules: either internal helpers or undocumented commands.

**Total ghost: 39**

| # | Module Name | Module Path | Tier |
|---|-------------|-------------|------|
| 1 | `agi` | `src/commands/agi.py` | misc |
| 2 | `analytics_commands` | `src/commands/analytics_commands.py` | misc |
| 3 | `analytics_show_commands` | `src/commands/analytics_show_commands.py` | misc |
| 4 | `auth_commands` | `src/commands/auth_commands.py` | misc |
| 5 | `autonomous_commands` | `src/commands/autonomous_commands.py` | misc |
| 6 | `build` | `src/commands/build.py` | misc |
| 7 | `ci` | `src/commands/ci.py` | misc |
| 8 | `clean` | `src/commands/clean.py` | misc |
| 9 | `compliance` | `src/commands/compliance.py` | misc |
| 10 | `config` | `src/commands/config.py` | misc |
| 11 | `core_commands` | `src/commands/core_commands.py` | misc |
| 12 | `dashboard_commands` | `src/commands/dashboard_commands.py` | founder |
| 13 | `debug_rate_limits` | `src/commands/debug_rate_limits.py` | engineering |
| 14 | `docs` | `src/commands/docs.py` | misc |
| 15 | `doctor` | `src/commands/doctor.py` | misc |
| 16 | `env` | `src/commands/env.py` | misc |
| 17 | `health_commands` | `src/commands/health_commands.py` | ops |
| 18 | `license_activation` | `src/commands/license_activation.py` | misc |
| 19 | `license_admin` | `src/commands/license_admin.py` | misc |
| 20 | `license_commands` | `src/commands/license_commands.py` | misc |
| 21 | `license_renewal` | `src/commands/license_renewal.py` | misc |
| 22 | `lint` | `src/commands/lint.py` | misc |
| 23 | `memory_commands` | `src/commands/memory_commands.py` | misc |
| 24 | `monitor` | `src/commands/monitor.py` | misc |
| 25 | `ocop_commands` | `src/commands/ocop_commands.py` | ops |
| 26 | `phase_commands` | `src/commands/phase_commands.py` | misc |
| 27 | `raas_maintenance_commands` | `src/commands/raas_maintenance_commands.py` | ops |
| 28 | `raas_validate` | `src/commands/raas_validate.py` | ops |
| 29 | `schedule_commands` | `src/commands/schedule_commands.py` | misc |
| 30 | `security_commands` | `src/commands/security_commands.py` | ops |
| 31 | `swarm_commands` | `src/commands/swarm_commands.py` | misc |
| 32 | `sync_commands` | `src/commands/sync_commands.py` | ops |
| 33 | `sync_raas` | `src/commands/sync_raas.py` | ops |
| 34 | `sync_raas_commands` | `src/commands/sync_raas_commands.py` | ops |
| 35 | `telegram_commands` | `src/commands/telegram_commands.py` | misc |
| 36 | `telemetry_commands` | `src/commands/telemetry_commands.py` | ops |
| 37 | `test_advanced` | `src/commands/test_advanced.py` | engineering |
| 38 | `tier_admin` | `src/commands/tier_admin.py` | misc |
| 39 | `usage_commands` | `src/commands/usage_commands.py` | misc |
