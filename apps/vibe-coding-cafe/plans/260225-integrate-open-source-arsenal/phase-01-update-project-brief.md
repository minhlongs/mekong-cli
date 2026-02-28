# Phase 01: Update `project-brief.html` with Tech Stack

## Overview
- Priority: High
- Current Status: Pending
- Brief: Add an Open Source Arsenal / Tech Stack section to the VIBE CODING `project-brief.html` based on the 12 pillars.

## Key Insights
- The café operates on 12 open-source pillars to reduce SaaS costs by 90% (e.g., Odoo, Cal.com, OpenWISP).
- Needs to be seamlessly integrated into the existing `project-brief.html` UI (dark mode, glassmorphism, glowing accents).

## Requirements
- Add a new `<section class="section">` in `project-brief.html`.
- Use a CSS Grid layout to highlight key tools (Odoo for POS/ERP, Cal.com for booking, OpenWISP for WiFi, Frigate for CCTV).
- Mention the cost savings (~21M VND initial, 700k/month).

## Related Code Files
- Modify: `project-brief.html`

## Implementation Steps
1. Locate the closing section of the business model or before the timeline in `project-brief.html`.
2. Insert a new section titled "💻 Tech Stack — Open Source Arsenal".
3. Add cards for top 4-6 tools (Odoo, Cal.com, OpenWISP, Home Assistant).
4. Save file.

## Todo List
- [ ] Edit `project-brief.html` to add Tech Stack UI.

## Success Criteria
- Opening `project-brief.html` locally shows the new Open Source Arsenal section styled consistently.