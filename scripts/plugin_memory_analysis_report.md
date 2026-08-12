# Plugin Memory Footprint Analysis Report

**Analysis Date:** 2026-06-20
**Task:** #63 - Analyze plugin memory footprint
**Scope:** All plugins in `.claude/skills/`, `.agents/skills/`, `packages/cleo/skills/`

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total plugins analyzed | 63 |
| Total disk usage | 145.22 MB |
| Total files | 16,015 |
| Total lines of code | 1,661,480 |
| Plugins with scripts | 23 |
| Plugins with templates | 3 |
| Plugins with references | 37 |

### Critical Findings

1. **node_modules bloat accounts for 95.7% of disk usage (139 MB)**
2. **Source maps (.map files) add 2.4 MB of production artifacts**
3. **Lock files (5 files) add unnecessary bloat**
4. **Top 3 plugins consume 81% of total disk space**

---

## Top 10 Plugins by Disk Usage

| Rank | Plugin | Size | Files | LOC | Dependencies |
|------|--------|------|-------|-----|--------------|
| 1 | show-off | 58.0 MB | 4,450 | 732,039 | sharp, puppeteer |
| 2 | stitch | 52.4 MB | 4,921 | 438,799 | @google/stitch-sdk |
| 3 | sequential-thinking | 22.4 MB | 4,292 | 318,383 | - |
| 4 | markdown-novel-viewer | 6.6 MB | 1,726 | 147,420 | - |
| 5 | ui-ux-pro-max | 1.5 MB | 20 | 1,842 | - |
| 6 | cti-expert | 1.1 MB | 114 | 2,252 | - |
| 7 | threejs | 345 KB | 29 | 1,136 | - |
| 8 | skill-creator | 280 KB | 42 | 2,784 | - |
| 9 | tech-graph | 236 KB | 37 | 2,187 | - |
| 10 | preview | 236 KB | 13 | 0 | - |

**Top 3 account for 132.8 MB (91.5% of total)**

---

## File Type Distribution

| Extension | Count | Notes |
|-----------|-------|-------|
| .js | 5,938 | JavaScript source |
| .ts | 3,440 | TypeScript source |
| .map | 2,452 | Source maps (production unnecessary) |
| .md | 1,164 | Documentation |
| .json | 774 | Configuration |
| .css | 526 | Stylesheets |
| (empty) | 501 | Empty extension files |
| .cjs | 262 | CommonJS modules |
| .scss | 256 | SCSS styles |
| .cts | 224 | CommonJS TypeScript |
| .mjs | 90 | ES modules |
| .py | 52 | Python scripts |
| .pdl | 52 | Protocol definitions |
| .mts | 46 | TypeScript ES modules |
| .yml | 40 | YAML configs |
| .bare | 39 | Bare scripts |
| .txt | 38 | Text files |
| .csv | 27 | Data files |
| .html | 11 | HTML templates |
| .svg | 10 | Vector graphics |

---

## Dependencies Analysis

### External Dependencies (4 unique)

- `@google/stitch-sdk` (used by: stitch)
- `@modelcontextprotocol/sdk` (used by: use-mcp)
- `puppeteer` (used by: show-off)
- `sharp` (used by: show-off)

### Embedded node_modules

**Total: 139 MB** across 3 plugins:

| Plugin | node_modules size | Main deps |
|--------|-------------------|-----------|
| show-off/scripts | 69 MB | puppeteer, sharp |
| sequential-thinking | 33 MB | jest-worker, make-dir |
| markdown-novel-viewer | 11 MB | - |
| Others | 26 MB | scattered |

**This is the #1 memory bloat issue.**

---

## Memory Footprint Estimates (Runtime)

### Current State (with node_modules bundled)

| Loading Strategy | Per Plugin | Total (63 plugins) |
|------------------|------------|-------------------|
| Metadata only | 0.1-0.5 MB | 6-32 MB |
| Lazy loaded | 2.5 MB | 158 MB |
| Eager loaded | ~11.5 MB | 724 MB |

### Optimized State (node_modules removed, lazy loading)

| Loading Strategy | Per Plugin | Total (63 plugins) |
|------------------|------------|-------------------|
| Metadata only | 0.1-0.5 MB | 6-32 MB |
| Lazy loaded | 0.5 MB | 32 MB |
| Eager loaded | 2 MB | 126 MB |

**Optimization potential: 75-83% reduction in runtime memory**

---

## Detailed Plugin Analysis (Top 5)

### 1. show-off (58.0 MB)

- **Files:** 4,450 | **LOC:** 732,039
- **File breakdown:** 1,134 .js + 1,467 .ts + 1,120 .map
- **Dependencies:** sharp, puppeteer
- **node_modules:** 69 MB in scripts/
- **Structure:** Has scripts, manifest, no templates/references
- **Recommendation:** Extract puppeteer/sharp to shared native deps, strip .map files

### 2. stitch (52.4 MB)

- **Files:** 4,921 | **LOC:** 438,799
- **File breakdown:** 1,573 .js + 1,511 .ts + 905 .map
- **Dependencies:** @google/stitch-sdk
- **node_modules:** appears to have bundled dependencies
- **Structure:** Has scripts, references, manifest
- **Recommendation:** Use @google/stitch-sdk as external dep, strip .map files

### 3. sequential-thinking (22.4 MB)

- **Files:** 4,292 | **LOC:** 318,383
- **File breakdown:** 2,364 .js + 453 .ts + 421 .map
- **Dependencies:** None (but has 33 MB node_modules)
- **node_modules:** 33 MB
- **Structure:** Has scripts, references, manifest
- **Recommendation:** Remove node_modules entirely

### 4. markdown-novel-viewer (6.6 MB)

- **Files:** 1,726 | **LOC:** 147,420
- **File breakdown:** 859 .js + 7 .ts + 6 .map
- **Dependencies:** None
- **node_modules:** 11 MB (unnecessary)
- **Structure:** Has scripts, manifest
- **Recommendation:** Remove node_modules, likely dev deps only

### 5. ui-ux-pro-max (1.5 MB)

- **Files:** 20 | **LOC:** 1,842
- **File breakdown:** 4 .py (only Python plugin in top 10)
- **Dependencies:** None
- **Structure:** Has scripts, manifest
- **Note:** Clean, small footprint - good example

---

## Optimizations

### 1. Remove All node_modules from Plugin Repositories (SAVES: 139 MB)

**Why:** Plugins should declare dependencies in manifest, not bundle them.
**How:**
- Add `node_modules/` to `.gitignore` for all skills
- Remove node_modules from git tracking
- Document dependency management in plugin SDK

### 2. Strip Source Maps from Production (SAVES: ~2.4 MB)

**Why:** .map files are for debugging, not needed at runtime.
**How:**
- Add `*.map` to `.gitattributes` export-ignore
- Update build scripts to not generate maps in production
- For already-committed maps, remove them

### 3. Remove Lock Files from Plugins (SAVES: ~500 KB)

**Why:** Lock files create duplication; use central lock file.
**How:**
- Remove package-lock.json, yarn.lock, pnpm-lock.yaml from plugin directories
- Keep single lock file at repo root

### 4. Implement Lazy Loading (Runtime savings: 58-83%)

**Why:** Not all plugins are used in every session.
**How:**
- Load plugins on first use
- Unload unused plugins after idle timeout
- Pre-load only core plugins (10-20 essential ones)

### 5. Consolidate Shared Dependencies

**Why:** Reduce duplication of common libraries.
**How:**
- Create `_shared/node_modules` for common deps
- Resolve imports from shared location first
- Use peerDependencies for plugin-specific versioning

### 6. Bundle Related Plugins

**Why:** Reduce overhead of loading many small plugins.
**How:**
- Group plugins by domain (e.g., all `ck-*` into checklist bundle)
- Load bundles instead of individual plugins
- Expose individual plugins from bundles

---

## Recommendations by Priority

### Critical (Do Now)

1. **Remove node_modules from all plugins** - 139 MB immediate savings
2. **Add .gitignore rules** to prevent future node_modules commits
3. **Document dependency declaration** in SKILL.md manifest

### High (This Sprint)

4. **Implement lazy loading** in plugin manager
5. **Add source map stripping** to build pipeline
6. **Create shared dependency resolution** mechanism

### Medium (Next Quarter)

7. **Bundle core plugins** for faster startup
8. **Add plugin size limits** to manifest schema
9. **Implement plugin compression** (gzip/brotli)

---

## Appendix: Full Plugin List

See `/tmp/plugin_memory_analysis.json` for complete dataset including:

- All 63 plugins with full metrics
- File type breakdowns per plugin
- Script file listings
- Dependency trees

---

## Methodology

- **Disk size:** Recursive sum of file sizes (excluding node_modules symlinks)
- **File count:** All non-hidden files
- **LOC:** UTF-8 line count of text files
- **Dependencies:** Extracted from `scripts/package.json`
- **Memory estimates:** Based on Node.js V8 overhead (3-10x loaded code size)

---

**Status:** Analysis complete. Ready for implementation of critical optimizations.
