# Brand Identity System Implementation Plan

## Objective
Implement the brand identity system and visual assets for the "Nhịp Điệu Xanh" platform in `/Users/macbook/nhipdieuxanh-agent/brand`.

## Proposed Milestones & Steps

### Milestone 1: Strategic Planning & Setup (Orchestrator)
- [x] Analyze `ORIGINAL_REQUEST.md`.
- [x] Create project tracking files (`PROJECT.md`, `progress.md`, `plan.md`, `BRIEFING.md`).
- [x] Initialize heartbeat safety timer.

### Milestone 2: Color and Typography Tokens (Worker + Reviewers)
- **Task**: Create `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json`.
- **Primary Color**: Emerald `#10B981`. Define light/medium/dark shades, neutral backgrounds, text, and semantic colors (success, warning, error).
- **Typography Scale**: Outfit (headings, weights 500, 600, 700) and Inter (body text, weights 400, 500). Define size scales in rem/px and line heights.
- **Target File**: `/Users/macbook/nhipdieuxanh-agent/brand/brand_tokens.json`.
- **Assigned Worker**: `teamwork_preview_worker`
- **Reviewer**: `teamwork_preview_reviewer`
- **Verification**: Verify JSON formatting and key presence.

### Milestone 3: SVG Logo Assets (Worker + Reviewers)
- **Task**: Generate four distinct SVG logo variations.
  1. `logo-primary.svg` (Full color with text "Nhịp Điệu Xanh" in Outfit font style and a creative symbol)
  2. `logo-monochrome.svg` (Black & White version, clean path details)
  3. `logo-symbol.svg` (The standalone icon representing green-energy + real-estate rhythm)
  4. `favicon.svg` (16x16 / 32x32 clean scalable icon representation)
- **Target Folder**: `/Users/macbook/nhipdieuxanh-agent/brand/logos/`
- **Assigned Worker**: `teamwork_preview_worker`
- **Reviewer**: `teamwork_preview_reviewer`
- **Verification**: Check XML structure validity, tags closed, attributes present, render preview if possible.

### Milestone 4: Brand Style Guide Document (Worker + Reviewers)
- **Task**: Compile style tokens and logos into `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html`.
- **Contents**:
  - Color palette display blocks showing primary, neutral, and semantic colors (and their HEX/HSL values).
  - Typography scale rendering text elements with Outfit/Inter fonts.
  - Logo showcase showing the generated SVG files.
  - Do's and Don'ts rules for logo usage, color pairings, typography.
- **Target File**: `/Users/macbook/nhipdieuxanh-agent/brand/guidelines.html`
- **Assigned Worker**: `teamwork_preview_worker`
- **Reviewer**: `teamwork_preview_reviewer`
- **Verification**: Ensure no broken asset links, valid HTML, valid styling.

### Milestone 5: Verification & Integrity Audit (Auditor)
- **Task**: Perform strict verification checks.
- **Audit Points**:
  - No hardcoded cheat outputs in source.
  - Valid XML for all SVGs.
  - Guidelines file is loadable and has correct layout.
  - All files are in their correct final locations.
