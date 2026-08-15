# Incremental Migration Strategy

**Last Updated**: 2026-06-20  
**Strategy**: Layer-by-layer with canary testing  
**Risk Level**: Low (gradual rollout with instant rollback)  
**Timeline**: 12 weeks total (6 layers × 2 weeks each)

---

## 1. Overview

This document outlines the incremental migration strategy from monolithic commands to the plugin system. The strategy prioritizes:

- **Safety**: No downtime, instant rollback
- **Observability**: Real-time metrics and alerts
- **User Experience**: Seamless transition with clear communication
- **Quality**: Comprehensive testing at each stage

---

## 2. Migration Architecture

### Dual-Runtime Support

```
┌─────────────────────────────────────────────┐
│         Mekong CLI (User Command)           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     Command Router (feature flag aware)     │
├─────────────────────────────────────────────┤
│  1. Check command cache                    │
│  2. Lookup: native OR plugin OR legacy     │
│  3. Route based on feature flags          │
│  4. Fallback chain: plugin → legacy → err  │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┴─────────────┐
    ▼                           ▼
┌─────────────┐       ┌──────────────────┐
│   Plugin    │       │   Legacy Shim    │
│  Registry   │       │   (Typer)        │
└─────────────┘       └──────────────────┘
```

### Feature Flag Matrix

```json
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": true
  },
  "feature_flags": {
    "plugin_founder": "shim",      // "plugin" | "legacy" | "shim"
    "plugin_business": "shim",
    "plugin_product": "legacy",
    "plugin_engineering": "legacy",
    "plugin_ops": "legacy",
    "plugin_studio": "legacy"
  }
}
```

Values:
- `"plugin"`: Use native plugin version
- `"legacy"`: Use legacy command module
- `"shim"`: Auto-select (plugin if available, else legacy)

---

## 3. Layer-by-Layer Rollout Plan

### Week 1-2: Founder Layer (52 commands)

**Risk**: Low  
**Complexity**: Simple commands, minimal dependencies  
**Rollback**: Instant via feature flag

#### Week 1: Canary (10% of commands)

```bash
# Enable founder plugins for test users
export MEKONG_FEATURE_PLUGIN_FOUNDER=plugin

# Monitor
watch -n 5 'mekong admin metrics --plugin-founder'
```

**Success Criteria**:
- Error rate < 0.1%
- Performance impact < 100ms
- No user complaints

#### Week 2: Full Rollout

```bash
# Enable for all users (update settings.json default)
jq '.feature_flags.plugin_founder = "plugin"' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# Deploy to production
# All users get founder plugin version
```

---

### Week 3-4: Business Layer (71 commands)

**Risk**: Medium  
**Complexity**: Medium commands, some external integrations

#### Week 3: Canary (10% of commands)

Enable: `sales`, `marketing`, `finance` (most-used)

**Additional Testing**:
- API integration tests
- Payment/billing flows
- External service connectivity

#### Week 4: Full Rollout

Enable all business commands.

---

### Week 5-6: Product Layer (31 commands)

**Risk**: Low-Medium  
**Complexity**: Simple to medium, mostly internal

**Focus**: 
- Performance benchmarking
- Load testing with concurrent users

---

### Week 7-8: Engineering Layer (66 commands)

**Risk**: HIGH  
**Complexity**: High, includes critical commands (`cook`, `code`, `deploy`)

#### Week 7: Extra Small Canary (5%)

Only enable for:
- Internal team accounts
- Automated test accounts
- Canary deployment group

**Intensive Monitoring**:
- Build times
- Test execution
- Deploy success rates

#### Week 8: Gradual Ramp

```
Day 1: 5% → 10%
Day 2: 10% → 25% (if metrics OK)
Day 3: 25% → 50%
Day 4: 50% → 100%
```

Each step requires manual approval from engineering lead.

---

### Week 9-10: Ops Layer (41 commands)

**Risk**: Medium-High  
**Complexity**: Complex, system-level operations

**Special Considerations**:
- Security audit before rollout
- Dry-run mode validation
- Backup verification

---

### Week 11-12: Studio Layer (23 commands)

**Risk**: Low  
**Complexity**: Smallest layer, specialized

---

## 4. Canary Testing Procedure

### Pre-Check

Before enabling any plugin:

```bash
# 1. Validate plugin
mekong admin plugin validate plugins/mekong-core-<layer>/

# 2. Load test
MEKONG_FEATURE_PLUGIN_<LAYER>=true time mekong <command> --help

# 3. Integration test
python3 -m pytest tests/integration/plugin_<layer>_commands.py -v
```

### Monitoring During Canary

**Metrics to Watch**:

| Metric | Baseline (Legacy) | Alert Threshold |
|--------|-------------------|-----------------|
| Command latency | TBD | > +500ms |
| Error rate | ~0% | > 0.1% |
| Memory usage | baseline | > +10% |
| Cold start time | N/A | > 5s |
| User complaints | 0 | > 5/hour |

**Dashboards**:
- Grafana: `Plugin System - <Layer>`
- Logs: `~/.mekong/logs/plugin-<layer>.log`

### Rollback Triggers

Auto-rollback if:
- ❌ Error rate > 0.5% (5-minute window)
- ❌ Latency > 2x baseline (5-minute window)
- ❌ Crash loop detected
- ❌ Manual override (engineering on-call)

**Rollback Command**:
```bash
mekong admin plugin disable mekong-core-<layer>
# OR
export MEKONG_FEATURE_PLUGIN_<LAYER>=legacy
```

---

## 5. Testing Strategy

### Unit Tests

Each plugin module must have:

```python
# tests/plugins/mekong-core-founder/test_handlers.py
def test_handle_annual():
    from plugins.mekong.core.founder.handlers.annual import handle_annual
    result = handle_annual(ctx=None, year=2025)
    assert result["status"] == "success"
```

Run: `pytest tests/plugins/ -v`

### Integration Tests

```python
# tests/integration/test_plugin_founder.py
def test_annual_command_works():
    result = subprocess.run(
        ["mekong", "annual", "--year", "2025"],
        capture_output=True,
        env={"MEKONG_FEATURE_PLUGIN_FOUNDER": "plugin"}
    )
    assert result.returncode == 0
    assert b"Annual report" in result.stdout
```

### Load Tests

```bash
# Simulate 100 concurrent users
python3 scripts/load-test-plugins.py \
  --concurrency 100 \
  --duration 60 \
  --command annual
```

---

## 6. Release Checklist

### Before Release

- [ ] All unit tests passing for plugin
- [ ] Integration tests passing
- [ ] Load tests meet SLA (< 5% overhead)
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Migration guide reviewed
- [ ] Rollback plan tested
- [ ] Monitoring dashboards ready
- [ ] On-call team notified
- [ ] User communication scheduled

### During Release

- [ ] Enable canary (10%)
- [ ] Monitor metrics for 24 hours
- [ ] Check user feedback channels
- [ ] Approve gradual increase
- [ ] Full rollout

### After Release

- [ ] Verify 100% traffic on plugin
- [ ] Legacy commands still available (as fallback)
- [ ] Document any issues
- [ ] Update migration status

---

## 7. Risk Mitigation

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Plugin crashes on load | Low | High | AST validation, sandboxing |
| Performance regression | Medium | Medium | Canary testing, benchmarks |
| Data corruption | Low | Critical | Dry-run mode, backups |
| Dependency conflict | Medium | High | Virtual environments, isolation |
| Security breach | Low | Critical | AST scanning, permissions |

### Operational Risks

| Risk | Mitigation |
|------|------------|
| User confusion | Clear deprecation notices, migration guides |
| Custom command breakage | Extended legacy support, migration tooling |
| Third-party plugin breakage | Compatibility testing, API versioning |
| Monitoring blind spot | Comprehensive metrics, logs |

---

## 8. Success Metrics

### Quantitative

- ✅ 100% of core commands migrated by v6.7
- ✅ Error rate < 0.1% during and after migration
- ✅ Performance impact < 5% (cold start < +500ms)
- ✅ 0 data loss incidents
- ✅ 95%+ user satisfaction (survey)

### Qualitative

- ✅ Clear migration path for custom command authors
- ✅ Comprehensive documentation
- ✅ Active community adoption
- ✅ Stable production deployments

---

## 9. Rollback Procedures

### Immediate Rollback (Single Layer)

```bash
# Disable problematic plugin
mekong admin plugin disable mekong-core-founder

# Or via feature flag
export MEKONG_FEATURE_PLUGIN_FOUNDER=legacy

# Restart services (if needed)
mekong platform restart gateway
```

### Full System Rollback

```bash
# Disable plugin system entirely
export MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED=false

# Or edit settings.json
jq '.plugin_system.enabled = false' ~/.mekong/settings.json > tmp && mv tmp ~/.mekong/settings.json

# Restart
mekong platform restart gateway
```

### Data Recovery

No data changes occur during migration (read-only by default). If write operations fail:

1. Plugin operations are atomic
2. Transactions rollback on error
3. Audit log captures all attempts
4. Manual reconciliation if needed

---

## 10. Post-Migration

After all layers complete:

### v6.8 - v6.9: Stabilization

- Bug fixes only
- Performance optimization
- Documentation updates

### v7.0: Legacy Removal

- Delete compatibility shim
- Remove `src/commands/` or archive
- Clean up feature flags
- Final migration check

---

**Approval Required**: Each layer rollout needs CTO sign-off  
**Emergency Contact**: See `docs/on-call-rota.md`  
**Last Review**: 2026-06-20
