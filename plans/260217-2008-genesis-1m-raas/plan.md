---
title: "GENESIS_1M_RAAS — Full Monorepo Scaffold từ ZERO"
description: "Scaffold hoàn chỉnh monorepo RaaS platform: Turborepo + Next.js + FastAPI + PostgreSQL + Docker"
status: pending
priority: P1
effort: 8h
branch: master
tags: [scaffold, monorepo, raas, genesis, infrastructure]
created: 2026-02-17
---

# GENESIS_1M_RAAS — Full Monorepo Scaffold từ ZERO

## Tổng Quan

Scaffold hoàn chỉnh RaaS platform monorepo structure từ zero, bao gồm:
- **Turborepo**: Monorepo orchestration
- **Frontend**: Next.js 14 App Router + TypeScript + Tailwind + Shadcn
- **Backend**: FastAPI Python API server
- **Database**: PostgreSQL + Prisma ORM
- **Agents**: `packages/openclaw-agents` shared package
- **Infrastructure**: docker-compose cho local dev

**Mục tiêu GENESIS**: "DOANH TRẠI ĐÃ SẴN SÀNG" — Frontend :3000, Backend :8000, docker-compose up → full stack running.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Monorepo | Turborepo + pnpm workspaces |
| Frontend | Next.js 14 App Router, TypeScript, Tailwind CSS, Shadcn UI |
| Backend | FastAPI 0.110+, Python 3.11+, Pydantic v2 |
| Database | PostgreSQL 16, Prisma ORM |
| Agents | Shared `packages/openclaw-agents` |
| Container | Docker + docker-compose |

---

## Architecture

```
raas-monorepo/
├── apps/
│   ├── web/                      # Next.js 14 frontend (:3000)
│   │   ├── app/                  # App Router
│   │   │   ├── page.tsx          # Landing page
│   │   │   └── layout.tsx        # Root layout
│   │   ├── components/           # React components
│   │   ├── lib/                  # Utilities
│   │   ├── public/               # Static assets
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.ts
│   │   └── next.config.js
│   └── api/                      # FastAPI backend (:8000)
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py           # FastAPI app + /health endpoint
│       │   ├── models.py         # Prisma models (User)
│       │   ├── routes/           # API routes
│       │   └── schemas/          # Pydantic schemas
│       ├── prisma/
│       │   └── schema.prisma     # Database schema
│       ├── requirements.txt
│       └── Dockerfile
├── packages/
│   └── openclaw-agents/          # Shared agent SDK
│       ├── src/
│       │   ├── index.ts          # Main export
│       │   └── types.ts          # Shared types
│       ├── package.json
│       └── tsconfig.json
├── docker-compose.yml            # PostgreSQL + app + api containers
├── turbo.json                    # Turborepo pipeline config
├── package.json                  # Root workspace config
├── pnpm-workspace.yaml           # pnpm workspaces
└── README.md                     # Setup instructions
```

---

## Phase 1: Monorepo Foundation

**Mục tiêu**: Khởi tạo Turborepo structure, install dependencies, config workspaces.

### 1.1 Root Setup

```bash
# Init monorepo
pnpm init
pnpm add -D turbo

# Create workspace config
cat > pnpm-workspace.yaml <<EOF
packages:
  - "apps/*"
  - "packages/*"
EOF

# Create turbo.json
cat > turbo.json <<EOF
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {
      "dependsOn": ["^lint"]
    }
  }
}
EOF
```

### 1.2 Frontend (apps/web)

```bash
# Create Next.js app with TypeScript + Tailwind
cd apps
npx create-next-app@latest web \
  --typescript \
  --tailwind \
  --app \
  --src-dir=false \
  --import-alias="@/*" \
  --no-experimental-app

# Install Shadcn
cd web
npx shadcn@latest init -y  # Default config

# Add button component (example)
npx shadcn@latest add button
```

**apps/web/package.json**:
```json
{
  "name": "@raas/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@radix-ui/react-slot": "^1.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.0",
    "postcss": "^8",
    "autoprefixer": "^10.4.0",
    "eslint": "^8",
    "eslint-config-next": "^14.2.0"
  }
}
```

### 1.3 Backend (apps/api)

```bash
# Create FastAPI structure
mkdir -p apps/api/app/routes
touch apps/api/app/__init__.py apps/api/app/main.py apps/api/app/models.py
mkdir apps/api/prisma

# Create requirements.txt
cat > apps/api/requirements.txt <<EOF
fastapi==0.110.0
uvicorn[standard]==0.27.1
pydantic==2.6.1
prisma==0.12.0
python-dotenv==1.0.1
EOF

# Install deps (in venv)
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**apps/api/app/main.py**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RaaS API", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "message": "RaaS API is running"}

@app.get("/")
async def root():
    return {"message": "Welcome to RaaS API"}
```

**apps/api/prisma/schema.prisma**:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider             = "prisma-client-py"
  recursive_type_depth = 5
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### 1.4 Shared Package (packages/openclaw-agents)

```bash
mkdir -p packages/openclaw-agents/src
cd packages/openclaw-agents

# package.json
cat > package.json <<EOF
{
  "name": "@raas/openclaw-agents",
  "version": "0.1.0",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "dependencies": {},
  "devDependencies": {
    "typescript": "^5.3.0"
  }
}
EOF

# tsconfig.json
cat > tsconfig.json <<EOF
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "declaration": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
EOF
```

**packages/openclaw-agents/src/index.ts**:
```typescript
export interface Agent {
  id: string;
  name: string;
  type: 'planner' | 'executor' | 'verifier';
}

export function createAgent(name: string, type: Agent['type']): Agent {
  return {
    id: crypto.randomUUID(),
    name,
    type,
  };
}
```

---

## Phase 2: Landing Page + /health API + User Schema

**Mục tiêu**: Tạo landing page đơn giản, verify API /health endpoint, generate Prisma client.

### 2.1 Landing Page (apps/web/app/page.tsx)

```tsx
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-5xl w-full text-center space-y-8">
        <h1 className="text-6xl font-bold text-gray-900">
          🌊 RaaS Platform
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Revenue-as-a-Service foundation for autonomous AI agencies.
          Powered by Plan-Execute-Verify intelligence.
        </p>

        <div className="flex gap-4 justify-center">
          <Button size="lg" className="text-lg">
            Get Started
          </Button>
          <Button size="lg" variant="outline" className="text-lg">
            Learn More
          </Button>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="p-6 bg-white rounded-lg shadow-sm">
            <h3 className="font-semibold text-lg mb-2">🧠 Autonomous</h3>
            <p className="text-gray-600">Plan-Execute-Verify workflow ensures systematic task handling</p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-sm">
            <h3 className="font-semibold text-lg mb-2">🦞 Orchestrated</h3>
            <p className="text-gray-600">Tôm Hùm daemon manages 24/7 mission dispatch</p>
          </div>
          <div className="p-6 bg-white rounded-lg shadow-sm">
            <h3 className="font-semibold text-lg mb-2">⚡ Intelligent</h3>
            <p className="text-gray-600">Antigravity Proxy optimizes LLM routing and cost</p>
          </div>
        </div>
      </div>
    </main>
  );
}
```

### 2.2 Verify API Health

```bash
# Start backend
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Test /health
curl http://localhost:8000/health
# Expected: {"status":"ok","message":"RaaS API is running"}
```

### 2.3 Generate Prisma Client

```bash
cd apps/api
prisma generate
prisma db push  # Apply schema to database (requires DATABASE_URL)
```

**.env** (apps/api):
```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/raas_dev"
```

---

## Phase 3: Dockerize All Services

**Mục tiêu**: docker-compose up → PostgreSQL + Frontend + Backend tất cả running.

### 3.1 Backend Dockerfile (apps/api/Dockerfile)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Generate Prisma client
RUN prisma generate

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Frontend Dockerfile (apps/web/Dockerfile)

```dockerfile
FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN corepack enable pnpm && pnpm build

# Production image
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
```

### 3.3 docker-compose.yml (root)

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    container_name: raas-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: raas_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: raas-api
    environment:
      DATABASE_URL: "postgresql://postgres:postgres@db:5432/raas_dev"
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./apps/api:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: raas-web
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    ports:
      - "3000:3000"
    depends_on:
      - api
    volumes:
      - ./apps/web:/app
      - /app/node_modules
      - /app/.next

volumes:
  postgres_data:
```

### 3.4 Verification Commands

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000

# Expected output:
# Backend: {"status":"ok","message":"RaaS API is running"}
# Frontend: HTML of landing page
```

---

## Success Criteria

- [ ] `pnpm install` từ root → install all workspaces
- [ ] `pnpm dev` từ root → start frontend :3000 + backend :8000
- [ ] Frontend landing page renders với Shadcn Button
- [ ] Backend /health endpoint returns `{"status":"ok"}`
- [ ] Prisma schema defined với User model
- [ ] `docker-compose up` → all 3 services (db + api + web) running
- [ ] `curl localhost:8000/health` → HTTP 200
- [ ] Browser `localhost:3000` → landing page visible
- [ ] Console output: **"DOANH TRẠI ĐÃ SẴN SÀNG"**

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Next.js 14 standalone output missing | Add `output: "standalone"` to next.config.js |
| Prisma Python client version mismatch | Pin `prisma==0.12.0` in requirements.txt |
| CORS errors between frontend/backend | Configure CORSMiddleware allow_origins |
| Docker build fails due to missing deps | Use multi-stage builds, cache layers |
| PostgreSQL not ready before API starts | Use `depends_on.condition: service_healthy` |

---

## Next Steps

1. **Authentication**: Integrate Supabase Auth or Better Auth
2. **Dashboard**: Add `/dashboard` route với user management
3. **Agent Integration**: Wire `packages/openclaw-agents` into frontend
4. **CI/CD**: GitHub Actions for build + deploy
5. **Production Deploy**: Vercel (frontend) + Railway/Fly.io (backend)

---

**Estimated Effort**: 8 hours
**Priority**: P1 (Foundation cần có trước khi implement features)
**Owner**: TBD (delegate to fullstack-developer agent)
