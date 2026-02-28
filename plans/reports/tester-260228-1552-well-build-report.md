# Build Report: apps/well (wellnexus-mvp)

## Build Status: ✅ SUCCESS

- **Project Name**: wellnexus-mvp
- **Build Command**: `npm run build`
- **Execution Time**: 9.78 seconds
- **Vite Version**: v7.3.1

## Pre-build Steps
- **Sitemap Generation**: ✅ Generated with 6 routes.
- **i18n Validation**: ✅ PASSED. Checked 1465 unique translation keys in `vi.ts` and `en.ts`.

## Build Metrics
- **Modules Transformed**: 3978
- **Total Bundle Size**: ~3.2 MB (uncompressed)
  - `index-BunqBsUd.css`: 230.67 kB
  - `pdf-o2Lr0QHW.js`: 1,574.32 kB (Largest chunk)
  - `index-CK_B2LX9.js`: 293.87 kB
- **Type Checking (tsc)**: ✅ PASSED (included in build command).

## Build Warnings/Errors
- None detected.

## Critical Issues
- None.

## Recommendations
- The `pdf-o2Lr0QHW.js` chunk is quite large (1.5 MB). Consider lazy loading or splitting if it impacts initial load performance.

## Next Steps
- Project is ready for deployment/integration tests.
