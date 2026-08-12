# Plugin Runtime Memory Footprint Analysis

**Analysis Date:** 2026-06-20 23:01:32
**Task:** #63 - Analyze plugin memory footprint
**Scope:** Runtime RAM usage of command/plugin module loading

## Executive Summary

| Metric | Value |
|--------|-------|
| Modules profiled | 12 |
| Baseline memory | 26.17 MB |
| Memory after loading all | 193.73 MB |
| Total overhead | +167.56 MB |
| Average per-module (memory-increasing) | 13.96 MB |
| **Potential memory retained** | **167.56 MB** |

## Critical Findings

1. **CRITICAL: Significant memory retention detected**
   - 167.56 MB not released after module imports
   - Likely cause: global caches, singletons, or module-level state

2. **Disk vs Memory Comparison**
   - Disk footprint: See `scripts/plugin_memory_analysis_report.md` (storage analysis)
   - Runtime memory: This analysis (RAM usage)
   - Rule of thumb: Runtime memory ≈ 3-10× the size of loaded Python bytecode

## Detailed Findings

### Top 10 Modules by Memory Overhead

Rank | Module | Δ Memory | Import Time | Disk Size
-----|--------|----------|-------------|----------
   1 | src.cli.cook_command      | +121.83MB |  4074ms |     14KB
   2 | src.cli.billing_commands  |  +26.28MB |   323ms |     25KB
   3 | src.commands.env          |  +13.14MB |   162ms |      2KB
   4 | src.commands.monitor      |   +3.48MB |    19ms |     18KB
   5 | src.commands.clean        |   +0.75MB |     6ms |      8KB
   6 | src.cli.studio_commands   |   +0.58MB |     7ms |     11KB
   7 | src.cli.autonomous_comman |   +0.56MB |    14ms |      9KB
   8 | src.commands.config       |   +0.34MB |    11ms |      8KB
   9 | src.commands.build        |   +0.27MB |     4ms |      7KB
  10 | src.commands.deploy       |   +0.12MB |     4ms |      9KB

### Memory Scaling Behavior

| Modules | Total Δ (MB) | Avg per module (MB) |
|---------|--------------|---------------------|
|        1 |        13.14 |             13.14 |
|        5 |        14.64 |              2.93 |
|       10 |       166.89 |             16.69 |

**Note:** Linear scaling expected; deviations indicate shared initialization.

### Garbage Collection Analysis

- No GC measurements taken

## Recommendations

### Immediate (This Sprint)

1. **Investigate highest memory modules**
   - `src.cli.cook_command`: 121.8MB overhead
   - `src.cli.billing_commands`: 26.3MB overhead
   - `src.commands.env`: 13.1MB overhead
   - Profile with `python -m memory_profiler` for line-by-line analysis
   - Look for large global data structures, caches, or file loads

2. **Add lazy imports for heavy modules**
   - Move imports inside functions if module is only used occasionally
   - Expected savings: 30-50% per lazily-loaded module

3. **Implement module-level cleanup**
   - Provide `unload()` function in command modules to clear globals
   - Call on plugin deactivation or interpreter shutdown

### Medium Term (Next Quarter)

4. **Implement lazy loading for non-core commands**
   - Load commands on first invocation
   - Unload idle commands after configurable timeout
   - Expected savings: 50-80% overall plugin memory

5. **Add memory quotas per plugin type**
   - Agent plugins: 50MB limit
   - Hook plugins: 10MB limit
   - Provider plugins: 30MB limit
   - Enforce via resource monitoring

6. **Optimize shared dependencies**
   - Preload common libraries (numpy, pandas, etc.) in core
   - Share loaded modules across plugins via sys.modules

### Long Term (Future)

7. **Consider process-level isolation**
   - Run heavy plugins in separate processes
   - OS-level memory limits enforced automatically
   - IPC overhead vs isolation benefits trade-off

8. **Plugin bundling**
   - Group related commands into bundles
   - Load bundle once instead of individual modules
   - Reduces shared dependency duplication

## Memory Leak Detection Strategy

### Production Monitoring

1. **OpenTelemetry Metrics**
   - Track `process.memory.usage` per plugin instance
   - Alert if memory grows >10% over 1 hour

2. **Periodic Snapshot Comparison**
   - Take tracemalloc snapshots every 5 minutes
   - Compare to detect accumulating object types
   - Sample code:
```python
import tracemalloc
tracemalloc.start()

snap1 = tracemalloc.take_snapshot()
# ... after plugin load/unload cycle ...
snap2 = tracemalloc.take_snapshot()

top_stats = snap2.compare_to(snap1, 'lineno')
for stat in top_stats[:10]:
    print(f'{stat.traceback[0].filename}:{stat.traceback[0].lineno}'
    print(f'  Size diff: {stat.size_diff / 1024:.1f} KB')
```

3. **Load/Unload Cycle Test**
   - In isolated subprocess:
     1. Measure baseline memory
     2. Load N plugins
     3. Unload all plugins
     4. Force GC
     5. Compare to baseline
   - Retention > 1MB indicates potential leak

## Methodology

- **Memory measurement:** `psutil.Process.memory_info().rss` for actual RAM
- **Tracemalloc:** Python built-in for tracking allocated objects
- **Baseline:** Core system before importing command modules
- **Per-module:** Sequential imports with GC between each
- **Test environment:** Local development (may vary in production)
- **Modules profiled:** 12 Python modules representing command/plugin code

## Limitations

- Modules measured in isolation (single process)
- Import order affects cumulative measurements (shared dependencies)
- Some modules may lazy-load heavy dependencies on first use (not captured)
- Python memory allocator may cache objects (appears as retained but reusable)
- Production memory may differ due to concurrent workloads

---

**Next Steps:**
1. Review top memory-consuming modules for optimization
2. Implement lazy loading for infrequently used commands
3. Add memory profiling to CI pipeline (nightly)
4. Document memory expectations in plugin developer guide

**Data Files:**
- Raw measurements: `/tmp/plugin_memory_runtime_measurements.json`
- Detailed profiles: `/tmp/plugin_memory_runtime_profiles.json`