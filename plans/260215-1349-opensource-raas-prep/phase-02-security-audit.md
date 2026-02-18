# Phase 2: Security & Privacy Audit

## Overview
- **Priority**: P1
- **Status**: Pending
- **Description**: Ensure the repository is clean of secrets, internal-only URLs, and sensitive business logic before going public.

## Requirements
- No hardcoded API keys or tokens.
- .env.example contains only placeholders.
- Internal-only documentation is redacted or relocated.

## Implementation Steps
1. **Secret Scan**:
   - Run grep/regex scans for keys.
   - Check `scripts/` and `apps/` specifically.
2. **Redact Internal Docs**:
   - Audit `apps/openclaw-worker/BINH_PHAP_MASTER.md` and similar files.
   - Remove or generalize internal rules that shouldn't be public.
3. **Gitignore Verification**:
   - Ensure logs and database files are correctly ignored.

## Todo List
- [ ] Perform full secret scan
- [ ] Redact internal files in openclaw-worker
- [ ] Verify .gitignore rules
- [ ] Update .env.example

## Success Criteria
- Zero hardcoded secrets in the repo history (squash might be needed if found).
- Internal business strategy is protected.
