# Research Report: Knowledge Item Restoration
**Date:** 2026-02-12
**Subject:** Restoration of Ethics, Self-Correction, and Meta-Learning Knowledge Items

## 1. Current State Analysis
The Knowledge Base at `~/.gemini/antigravity/knowledge/` is missing explicit domains for "Ethics", "Self-Correction", and "Meta-Learning". However, the functional logic for these domains exists within the `mekong-cli` codebase, specifically in the `src/core/` module.

### Mapping Code to Knowledge Domains

| Domain | Source File | Class | Description |
| :--- | :--- | :--- | :--- |
| **Ethics** | `src/core/governance.py` | `Governance` | Enforces safety boundaries via `FORBIDDEN_PATTERNS` (e.g., `rm -rf`, `drop table`) and `REVIEW_PATTERNS`. Maintains audit trails. |
| **Self-Correction** | `src/core/self_improve.py` | `SelfImprover` | Analyzes execution success/failure. Deprecates recipes with success rate < 20%. Suggests new recipes from successful manual interventions. |
| **Meta-Learning** | `src/core/learner.py` | `PatternAnalyzer` | Detects patterns like "Repeated Failures" (streak >= 3) and "Time-of-Day Correlations". Adapts system behavior based on historical memory. |

## 2. Target Structure
To restore these as proper Knowledge Items, we should follow the AgencyOS Knowledge Base structure observed in `agencyos_mekong_cli_raas_engine`:

**Directory Structure:**
```
~/.gemini/antigravity/knowledge/
  ├── agencyos_ethics_safety_governance/
  │     ├── metadata.json
  │     └── artifacts/
  │           ├── governance_policy.md
  │           └── forbidden_patterns.json
  ├── agencyos_self_correction_evolution/
  │     ├── metadata.json
  │     └── artifacts/
  │           ├── evolution_journal_spec.md
  │           └── deprecation_logic.md
  └── agencyos_meta_learning_patterns/
        ├── metadata.json
        └── artifacts/
              ├── pattern_recognition_rules.md
              └── failure_analysis.md
```

## 3. Implementation Strategy
1.  **Extract**: Pull logic, constants, and docstrings from the python files.
2.  **Format**: Convert extracted data into Markdown artifacts and JSON metadata.
3.  **Restore**: Create the directories and files in the Knowledge Base path.
4.  **Verify**: Ensure the Knowledge Base index (if any) recognizes these new items.

## 4. Unresolved Questions
- Is there a central index file for the Knowledge Base that needs updating, or is it directory-based discovery? (Current assumption: Directory-based discovery based on `ls` output).
