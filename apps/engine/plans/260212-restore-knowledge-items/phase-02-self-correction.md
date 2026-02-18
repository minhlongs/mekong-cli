# Phase 2: Self-Correction & Evolution Restoration

## Context
Restore the Self-Correction domain in the Knowledge Base by extracting logic from `src/core/self_improve.py`.

## Implementation Steps

1.  **Create Directory**
    - Path: `~/.gemini/antigravity/knowledge/agencyos_self_correction_evolution/artifacts/`

2.  **Create Metadata**
    - File: `~/.gemini/antigravity/knowledge/agencyos_self_correction_evolution/metadata.json`
    - Content: Title "AgencyOS Self-Correction & Evolution", summary regarding recipe optimization.

3.  **Create Artifacts**
    - File: `~/.gemini/antigravity/knowledge/agencyos_self_correction_evolution/artifacts/evolution_mechanics.md`
    - Content:
        - **Deprecation Logic**: Recipes with `< 20%` success rate after `10` runs are deprecated.
        - **Generative Logic**: New recipes created from manual goals that succeed.
        - **Journaling**: Tracking of `generated` vs `deprecated` actions.

## Validation
- Check directory exists.
- Check files exist.
