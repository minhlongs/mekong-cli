# SEO Meta Optimization Report

**Date:** 2026-03-23
**File:** `packages/raas-landing/src/layouts/base-layout.astro`

## Audit Result

The layout already had a solid meta foundation:
- `<meta name="description">` present
- `<meta name="keywords">` present with language variants
- `<link rel="canonical">` present
- `<meta name="robots">` present
- Twitter card tags: all 8 tags present
- OG tags: complete
- `<meta name="author">` present

## Changes Made

### 1. Default page title (line 21)
- Before: `'OpenClaw — AI Vận Hành Doanh Nghiệp Tự Động'`
- After: `'OpenClaw — AI Agent Platform: Robot as a Service cho Doanh Nghiệp'`
- Reason: injects "AI agent platform" + "robot as a service" into `<title>` — highest-weight SEO signal.

### 2. Default meta description (line 22)
- Before: generic VI description, no target keywords
- After: leads with "OpenClaw", includes "AI agent" + "Robot as a Service" (152 chars, within 160 limit)
- Reason: description appears in SERPs; keyword inclusion improves CTR and relevance signals.

### 3. Default keywords string — EN (line 58)
- Added: `AI agent platform, robot as a service, AI business automation, automate business AI, openclaw` at the front
- Reason: positions target terms before the existing long-tail list.

### 4. Default keywords string — VI (line 59)
- Added: `AI agent platform, robot as a service, openclaw, automate business AI` at the front
- Reason: same rationale; EN keywords kept for international indexing even on VI version.

## Not Changed
- OG tags — already well-formed, no edits needed
- Twitter card tags — complete, no edits needed
- `<meta name="author">` — "OpenClaw by AgencyOS" already present
- `<meta name="robots">` — already `index, follow` by default
- Canonical URL logic — already correct
