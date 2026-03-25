# Cloudflare Skill — Best Practices

## Standards
- Workers: < 1MB bundle size, < 10ms CPU time target
- Pages: static-first, SSR only when necessary
- D1 for SQL, KV for key-value, R2 for object storage
- Wrangler CLI for all deployments

## Patterns
- Edge-first architecture: compute at the edge
- KV for config/feature flags (eventual consistency OK)
- D1 for transactional data (SQLite-compatible)
- R2 for user uploads and static assets

## Gotchas
- Workers have no filesystem — use KV/R2
- D1 has row size limits (2KB per row recommended)
- KV writes propagate in ~60 seconds globally
- `wrangler dev` uses different runtime than production
- Free tier: 100K requests/day for Workers

## Deploy
- Frontend: `git push` triggers Pages build
- Backend: `wrangler deploy` for Workers
- Zero-cost stack: Pages + Workers + D1 + KV + R2
