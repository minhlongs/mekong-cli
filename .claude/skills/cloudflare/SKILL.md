---
name: cloudflare
description: |
  Comprehensive Cloudflare platform reference for AI/LLM consumption. Covers Workers, Pages, D1, R2, KV, Durable Objects, Workers AI, Vectorize, Agents SDK, networking, security, and infrastructure-as-code. Use for any Cloudflare deployment, edge computing, or serverless tasks.
when_to_use: "Invoke for any Cloudflare deployment, edge computing, serverless tasks, Workers/D1/R2/KV operations, or infrastructure-as-code with Cloudflare."
license: MIT
version: 1.0.0
based_on: https://github.com/dmmulroy/cloudflare-skill
---

# 🌩️ Cloudflare Skill

Comprehensive Cloudflare platform reference optimized for AI/LLM consumption.

## When to Use This Skill

Use this skill when:

- Deploying serverless functions to Cloudflare Workers
- Hosting static sites on Cloudflare Pages
- Setting up databases (D1) or key-value stores (KV)
- Managing object storage (R2)
- Building real-time applications (Durable Objects, WebSockets)
- Implementing AI/ML at the edge (Workers AI, Vectorize)
- Configuring security (WAF, DDoS, Bot Management, Turnstile)
- Automating with Terraform or Pulumi

## Decision Trees

### 🏃 Running Code

```
Need to run code?
├── Static site with some dynamic routes → Pages
├── API or webhook handler → Workers
├── Long-running stateful logic → Durable Objects
├── Multi-step async jobs → Workflows
├── Full container workload → Containers (beta)
└── Scheduled tasks → Workers + Cron Triggers
```

### 💾 Storage

```
Need to store data?
├── Key-value (simple, fast reads) → KV
├── Relational/SQL queries → D1
├── Large files/blobs → R2
├── Message queues → Queues
├── Vector embeddings → Vectorize
└── Session/state per user → Durable Objects
```

### 🤖 AI/ML

```
Need AI capabilities?
├── Run inference at edge → Workers AI
├── Store embeddings → Vectorize
├── Build AI agents → Agents SDK
├── Rate limit/log AI calls → AI Gateway
└── Generate images → Workers AI (Stable Diffusion)
```

### 🌐 Networking

```
Need networking?
├── Expose internal services → Tunnel (cloudflared)
├── TCP/UDP proxying → Spectrum
├── Real-time video/audio → Calls (WebRTC)
└── DNS management → DNS API
```

### 🔒 Security

```
Need security?
├── Web application firewall → WAF
├── DDoS protection → DDoS (automatic)
├── Bot detection → Bot Management
├── Human verification → Turnstile (CAPTCHA alternative)
├── Access control → Access (Zero Trust)
└── API protection → API Shield
```

### 🎬 Media

```
Need media processing?
├── Image optimization → Images
├── Video streaming → Stream
├── PDF/screenshot generation → Browser Rendering
└── Real-time video → Calls
```

## Quick Start

### Deploy a Worker

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Create project
wrangler init my-worker
cd my-worker

# Local development
wrangler dev

# Deploy
wrangler deploy
```

### Deploy a Pages Site

```bash
# For static site
wrangler pages deploy ./dist

# For full-stack (with functions)
# Put API routes in /functions folder
wrangler pages deploy ./
```

### Create D1 Database

```bash
# Create database
wrangler d1 create my-db

# Add to wrangler.toml
[[d1_databases]]
binding = "DB"
database_name = "my-db"
database_id = "<id-from-create>"

# Run migrations
wrangler d1 execute my-db --file=./schema.sql
```

### Create R2 Bucket

```bash
# Create bucket
wrangler r2 bucket create my-bucket

# Add to wrangler.toml
[[r2_buckets]]
binding = "BUCKET"
bucket_name = "my-bucket"
```

### Create KV Namespace

```bash
# Create namespace
wrangler kv:namespace create "MY_KV"

# Add to wrangler.toml
[[kv_namespaces]]
binding = "MY_KV"
id = "<id-from-create>"
```

## Reference Navigation

### Core Compute

- `references/workers/` - Serverless functions at the edge
- `references/pages/` - Static hosting + edge functions
- `references/durable-objects/` - Stateful compute
- `references/workflows/` - Multi-step async jobs

### Storage

- `references/d1/` - SQLite database with global replication
- `references/kv/` - Key-value store (fast reads)
- `references/r2/` - S3-compatible object storage (zero egress)
- `references/queues/` - Message queues

### AI/ML

- `references/workers-ai/` - Inference at the edge
- `references/vectorize/` - Vector database
- `references/agents-sdk/` - AI agent framework
- `references/ai-gateway/` - AI request management

### Security

- `references/waf/` - Web application firewall
- `references/turnstile/` - CAPTCHA alternative
- `references/access/` - Zero Trust access

### Media

- `references/images/` - Image optimization
- `references/stream/` - Video streaming
- `references/browser-rendering/` - Headless browser

## Common Patterns

### API with Database

```javascript
// Worker with D1
export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (url.pathname === "/users") {
            const { results } = await env.DB.prepare(
                "SELECT * FROM users LIMIT 10",
            ).all();
            return Response.json(results);
        }

        return new Response("Not found", { status: 404 });
    },
};
```

### File Upload to R2

```javascript
export default {
    async fetch(request, env) {
        if (request.method === "PUT") {
            const key = new URL(request.url).pathname.slice(1);
            await env.BUCKET.put(key, request.body);
            return new Response(`Uploaded ${key}`);
        }
        return new Response("Method not allowed", { status: 405 });
    },
};
```

### Caching with KV

```javascript
export default {
    async fetch(request, env) {
        const cacheKey = new URL(request.url).pathname;

        // Check cache
        const cached = await env.CACHE.get(cacheKey);
        if (cached) return new Response(cached);

        // Fetch and cache
        const data = await fetchExpensiveData();
        await env.CACHE.put(cacheKey, data, { expirationTtl: 3600 });

        return new Response(data);
    },
};
```

## Best Practices

### Performance

- Use KV for frequently read, rarely written data
- Use D1 for complex queries and transactions
- Use R2 for large files (zero egress fees!)
- Cache at the edge with Cache API

### Security

- Never expose API keys in client code
- Use Wrangler secrets: `wrangler secret put API_KEY`
- Validate all inputs
- Use Turnstile for bot protection

### Cost Optimization

- R2 has zero egress fees (vs S3)
- Workers have generous free tier (100k req/day)
- D1 free tier: 5M reads, 100k writes/day
- KV free tier: 100k reads, 1k writes/day

## Resources

- **Docs:** https://developers.cloudflare.com
- **Discord:** https://discord.cloudflare.com
- **Status:** https://www.cloudflarestatus.com
- **Wrangler:** https://developers.cloudflare.com/workers/wrangler/
