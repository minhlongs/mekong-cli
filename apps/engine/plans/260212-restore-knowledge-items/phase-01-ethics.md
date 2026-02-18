# Phase 1: Ethics & Governance Restoration

## Context
Restore the Ethics domain in the Knowledge Base by extracting governance logic from `src/core/governance.py`.

## Implementation Steps

1.  **Create Directory**
    - Path: `~/.gemini/antigravity/knowledge/agencyos_ethics_safety_governance/artifacts/`

2.  **Create Metadata**
    - File: `~/.gemini/antigravity/knowledge/agencyos_ethics_safety_governance/metadata.json`
    - Content: Define title "AgencyOS Ethics & Safety Governance", summary, and references to `governance.py`.

3.  **Create Artifacts**
    - File: `~/.gemini/antigravity/knowledge/agencyos_ethics_safety_governance/artifacts/governance_protocols.md`
    - Content:
        - **Forbidden Patterns**: `rm -rf`, `drop table`, `delete all`, etc.
        - **Review Patterns**: `deploy prod`, `push main`, `migrate`.
        - **Audit System**: Description of `AuditEntry` and storage in `.mekong/audit.yaml`.

## Validation
- Check directory exists.
- Check files exist and contain extracted logic.
