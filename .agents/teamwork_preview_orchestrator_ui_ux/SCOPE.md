# Scope: CRM Web App UI/UX Audit and Polish

This document defines the implementation scope, target files, and milestones for auditing and polishing the Next.js CRM Web App UI/UX to conform to the `ui-ux-pro-max` style guide.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|--------------|--------|
| 1 | M1: Dark Mode & Focus States for Kanban Card | Upgrading `web/components/pipeline/kanban-card.tsx` with dark mode styles and drag handle focus rings. | None | IMPLEMENTED |
| 2 | M2: Accessibility Focus Rings (Sidebar & Table) | Adding focus indicators to sidebar links in `web/components/app-sidebar-nav.tsx` and leads table rows in `web/app/app/leads/page.tsx`. | None | IMPLEMENTED |
| 3 | M3: Dashboard Responsiveness & Touch Targets | Fixing project cards overflow on 375px mobile screen and increasing buttons to 44px min touch target in `web/app/app/page.tsx`. | None | IMPLEMENTED |
| 4 | M4: E2E Test Case 2 Remediation | Adjusting Playwright locator in `web/tests/e2e/nhipdieuxanh.spec.ts` to assert on card placement instead of transient toast. | None | IMPLEMENTED |
| 5 | M5: Verification & Gate | Run `pytest` (backend), `npm run test` (frontend), and `npx playwright test` (E2E) to verify 100% pass. | M1, M2, M3, M4 | IN_PROGRESS |

## Detailed File Modifications

### 1. Kanban Card (`web/components/pipeline/kanban-card.tsx`)
- Refactor the card container class: add `dark:bg-slate-900 dark:border-zinc-800` (or semantic variables) to support dark mode.
- Add `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none` classes to the drag handle button.

### 2. Sidebar Navigation (`web/components/app-sidebar-nav.tsx`)
- Add focus ring outline classes (`focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:outline-none`) to the navigation links (`<Link>`) and dropdown triggers.

### 3. Leads Table (`web/app/app/leads/page.tsx`)
- Add focus states (e.g. `focus-visible:bg-accent/50 focus-visible:outline-none`) to the table rows (`<tr>` with `tabIndex={0}`).

### 4. Dashboard (`web/app/app/page.tsx`)
- Wrap project recommendation card info section in `flex-wrap` or responsive flex classes to handle 375px screen layout wrap.
- Change recent posts action buttons from `size="sm"` to default size or add custom class ensuring 44px minimum touch target height on mobile.

### 5. E2E Test Case 2 (`web/tests/e2e/nhipdieuxanh.spec.ts`)
- Modify line 130 (or surrounding test logic) to check that the card "Nguyễn Văn An" is in the column "Đã liên hệ" instead of expecting the transient toast text to be visible.
