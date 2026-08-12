## Quickstart

### Prerequisites


- Python 3.11+
- Node.js 20+ (frontend)
- Cloudflare account (Wrangler)

### Setup Steps


1. Clone repo & enter project

2. Copy `.env.example` → `.env`; fill secrets

3. `npm install` (root + app)

4. `npx wrangler d1 create <db>` — copy DB ID

5. Apply migrations: `bash scripts/apply-migrations.sh`

6. `npm run dev` — confirm `localhost:3000`

### Verify


`npm run build && npm test`
