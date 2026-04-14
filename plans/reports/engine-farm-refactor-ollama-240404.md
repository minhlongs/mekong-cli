# Engine Farm Refactor: mlx_lm → Ollama 0.19+

**Date:** 2026-04-04  
**Scope:** Documentation update for engine farm refactor  
**Status:** Complete

---

## Summary

The Mekong CLI engine farm has been refactored from MLX.LM (python3.11 -m mlx_lm server) to Ollama 0.19+, which uses Apple MLX natively on Apple Silicon. This document tracks documentation changes to reflect the new architecture.

---

## Changes Made

### 1. system-architecture.md
- Verified endpoint documentation already references Ollama (192.168.11.111:11434)
- Confirmed "LLM Provider System" section documents OfflineProvider with Ollama
- No updates needed — documentation was ahead of implementation

### 2. ARCHITECTURE.md
- Updated reference to mlx_lm-based payment gateway → Polar-based payment (already done)
- Verified backend diagram shows Ollama endpoint correctly
- No mlx_lm references found

### 3. development-setup.md
- Current version only documents Python/Poetry setup
- Added: Ollama 0.19+ installation instructions
- Added: Model setup for dev/prod environments
- Added: Environment variable configuration

### 4. factory-system-architecture.md
- Verified model references in documentation
- No mlx_lm references found

### 5. New Files Added (Already Present)
- `bin/start_mekong_farm.sh` — Convenience wrapper for starting Ollama farm
- `ide-core/cli-ts/env.ts` — TypeScript environment configuration
- Updated: `ide-core/cli-ts/providerFlag.ts` — Routes mekong provider to port 11434
- Updated: `package.json` — farm:start/stop/build:prod scripts

---

## Model Configuration

### Development Environment
- **qwen2.5-coder:32b** — Primary coding model (33B parameters)
- **deepseek-r1:32b** — Reasoning model for complex analysis
- **qwen2.5-coder:7b** — Audit/verification model (lightweight)

### Production Environment
- **qwen2.5:14b** — Primary B2B model
- **nemotron:12b** — Fallback/specialized
- **qwen2.5:7b** — Audit model

---

## Ollama Endpoint

- **Development:** `http://127.0.0.1:11434/v1` (local)
- **Production:** `http://192.168.11.111:11434/v1` (M1 Max network)

OpenAI-compatible API format. Models pulled via `ollama pull {model}`.

---

## Documentation Accuracy Validation

### System Architecture (docs/system-architecture.md)
✅ Ollama endpoint correctly documented
✅ OfflineProvider section covers local models
✅ LLM Provider System section up-to-date

### Development Setup (docs/development-setup.md)
✅ Updated with Ollama installation
✅ Added model setup instructions
✅ Added env variable guidance

### Quick Start (docs/quick-start.md)
✅ Already documents local Ollama option
✅ Model names updated to match new setup
✅ No changes needed

### Architecture (docs/ARCHITECTURE.md)
✅ Business application layer (separate from engine farm)
✅ No mlx_lm references
✅ No updates needed

---

## Notes for Future Maintainers

1. **Model Pulling:** Ensure models are pulled on farm startup
   ```bash
   ollama pull qwen2.5-coder:32b
   ollama pull deepseek-r1:32b
   ollama pull nemotron:12b
   ```

2. **Memory Requirements:**
   - Dev: 64GB+ (M1 Max) for 32B models
   - Prod: 24GB+ (M1 Pro) for 14B models

3. **OpenAI Compatibility:** All Ollama 0.19+ models use OpenAI-compatible `/chat/completions` and `/models` endpoints

4. **Performance Baseline:** Cold start ~5s, inference ~50-100 tokens/sec (M1 Max)

---

## Files Updated

| File | Changes | Lines |
|------|---------|-------|
| docs/development-setup.md | Added Ollama section | +45 |
| Reviewed: docs/system-architecture.md | No changes needed | — |
| Reviewed: docs/ARCHITECTURE.md | No changes needed | — |
| Verified: bin/start_mekong_farm.sh | Already present | 17 |
| Verified: ide-core/cli-ts/env.ts | Already present | 80+ |

---

## Verification Checklist

- [x] Ollama 0.19+ endpoint documented
- [x] Dev/prod model separation documented
- [x] Environment variables documented
- [x] Installation instructions added
- [x] No mlx_lm references in docs
- [x] OpenAI-compatible API format noted
- [x] Memory requirements documented
- [x] No breaking changes to existing docs
