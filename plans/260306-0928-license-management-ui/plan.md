---
title: "License Management UI - Next.js Frontend"
description: "Implement License Management page at /license route in Next.js frontend with React hooks, Tailwind CSS, and API integration"
status: pending
priority: P2
effort: 3h
branch: master
tags: [license, ui, nextjs, react, raas]
created: 2026-03-06
---

# License Management UI Implementation Plan

## Context Links
- Backend API: `src/api/license_ui.py`
- Existing template: `src/api/templates/license_dashboard.html`
- Frontend: `/Users/macbookprom1/mekong-cli/frontend/landing`
- Report: `plans/reports/planner-260306-0928-license-management-ui.md`

## Overview
Implement Next.js React component for license management, replacing the existing FastAPI HTML template with a modern React UI at `/license` route.

## Key Insights
- Backend already has 4 API endpoints: `/api/status`, `/api/activate`, `/api/validate`, `/api/deactivate`
- Existing HTML template provides UX reference for status badges, forms, alerts
- Frontend uses Next.js 16, React 19, Tailwind CSS 4, TypeScript 5
- Existing UI components: Card, Tabs, GlassCard available in `components/ui/`

## Requirements

### Functional
- Display current license status (active/invalid/no_license)
- Show tier and enabled features when valid
- Activate license with key validation
- Validate license without activating
- Deactivate current license
- Real-time feedback with loading states

### Non-Functional
- TypeScript strict typing
- Responsive design (mobile-first)
- Tailwind CSS styling matching existing landing page
- Error handling with user-friendly messages

## Architecture

### Component Hierarchy
```
/license (page.tsx)
├── LicenseDashboard
│   ├── StatusCard
│   │   ├── StatusBadge (active/invalid/no_license)
│   │   └── FeaturesList
│   ├── ActivateCard
│   │   ├── LicenseForm
│   │   └── ActionButtons (Activate/Validate/Deactivate)
│   └── HelpCard
└── API hooks (useLicense)
```

### API Integration
- Use React Query or native fetch with React hooks
- API base URL: `http://localhost:8080` (FastAPI backend)
- CORS must be enabled on backend

## Related Code Files

### Create
- `frontend/landing/app/license/page.tsx` - Main page component
- `frontend/landing/components/license/LicenseDashboard.tsx` - Dashboard container
- `frontend/landing/components/license/StatusCard.tsx` - Status display
- `frontend/landing/components/license/ActivateCard.tsx` - Activation form
- `frontend/landing/components/license/HelpCard.tsx` - Help/info card
- `frontend/landing/components/license/index.ts` - Exports
- `frontend/landing/hooks/useLicense.ts` - API hook
- `frontend/landing/lib/license/types.ts` - TypeScript types

### Modify
- None (new feature, no existing files modified)

## Implementation Steps

### Step 1: TypeScript Types
Create type definitions for API responses and state.

### Step 2: API Hook
Create `useLicense` hook with:
- `useStatus()` - GET /api/status
- `useActivate()` - POST /api/activate
- `useValidate()` - POST /api/validate
- `useDeactivate()` - POST /api/deactivate

### Step 3: UI Components
Build reusable components:
- StatusBadge with color variants
- FeaturesList grid
- LicenseForm with validation
- Alert component for feedback

### Step 4: Page Assembly
Compose components in `/license/page.tsx`

### Step 5: Styling
Apply Tailwind classes matching existing design system

## Todo List
- [ ] Create TypeScript types for license data
- [ ] Create useLicense hook with API calls
- [ ] Create StatusCard component
- [ ] Create ActivateCard component
- [ ] Create HelpCard component
- [ ] Create main license page
- [ ] Test API integration
- [ ] Verify responsive design

## Success Criteria
- Page renders at http://localhost:3000/license
- Status loads correctly on page load
- Activate/Validate/Deactivate work with real API
- Loading states show during async operations
- Error messages display for failed operations
- Mobile responsive (tested at 375px width)

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| CORS errors | High | Enable CORS in FastAPI app |
| API port mismatch | Medium | Use env var for API_BASE_URL |
| TypeScript errors | Low | Strict typing from start |

## Security Considerations
- License key stored in `.env` file (backend responsibility)
- No sensitive data in client-side state
- Input validation on license key format

## Next Steps
1. Review and approve plan
2. Implement Step 1-2 (types + hook)
3. Implement Step 3-4 (components + page)
4. Test integration with running backend
