# Documentation Update: Clipmart Templates Addition

**Date:** 2026-04-04  
**Scope:** Add clipmart/ directory documentation to existing docs  
**Files Updated:** 2  
**Status:** Complete

---

## Summary

The `clipmart/` directory containing 3 Paperclip AI company templates has been integrated into the project documentation. These pre-built agent teams represent a new capability for developers and founders to bootstrap AI companies.

---

## Changes Made

### 1. codebase-summary.md

**Location:** `/docs/codebase-summary.md`

**Changes:**
- Updated "Applications & Company Templates" section to include clipmart/ directory structure
- Added new "Company Templates (Clipmart)" section (14 lines) with:
  - Template comparison table (mekong-saas-startup, mekong-dev-shop, mekong-solo-founder)
  - Feature summary per template
  - Quick start example
  - Updated "Next Steps" to reference clipmart

**Lines added:** 24

### 2. project-overview-pdr.md

**Location:** `/docs/project-overview-pdr.md`

**Changes:**
- Enhanced "Key Features Breakdown" section to include company templates
- Added "Company Templates (Clipmart)" as 4th major feature alongside PEV Pipeline, Agent System, Credit Billing, DAG Execution
- Documented template descriptions and key characteristics

**Lines added:** 7

---

## Template Inventory

| Template | Agents | Skills | Use Case |
|----------|--------|--------|----------|
| **mekong-saas-startup** | 22 | 323+ | SaaS founders, funded companies, full org structure |
| **mekong-dev-shop** | 8 | 150+ | Dev agencies, engineering teams, SRE/security/QA focused |
| **mekong-solo-founder** | 5 | 100+ | Solopreneurs, lean startups, MVP shipping |

---

## Architecture

Each template includes:
- **Org charts** with agent roles and reporting structure
- **Binh Pháp governance** (Sun Tzu's Art of War chapters per agent)
- **Skills** aligned to roles (cook, deploy, test, market, finance, legal, etc.)
- **Escalation matrices** (L0-L3 decision authority)
- **Team organization** (Revenue, Product, Engineering, Operations, Strategy)
- **README with quick-start** instructions

---

## Verification

All documentation changes maintain:
- Consistency with existing Mekong CLI documentation style
- Links to clipmart/ directory paths verified to exist
- References accurate to template README files
- No broken links or references

---

## Next Steps (Optional)

1. Create `docs/clipmart-guide.md` if more detailed template documentation needed (currently covers in project-overview)
2. Update README.md root file to mention company templates in "Install" section (if marketing focus)
3. Add Paperclip CLI integration docs in `docs/getting-started.md` (future)

---

## File Paths

- `/Users/macbookprom1/mekong-cli/docs/codebase-summary.md` — Updated
- `/Users/macbookprom1/mekong-cli/docs/project-overview-pdr.md` — Updated
- `/Users/macbookprom1/mekong-cli/clipmart/` — Verified (3 templates exist)

