---
name: Deploy Cloudflare Workers
platforms: cloudflare
---

# Deploy Cloudflare Workers

Deploy your application to Cloudflare Workers platform.

## Step 1: Build the project

npm run build

## Step 2: Update wrangler.toml

Make sure wrangler.toml is configured with correct name and route.

## Step 3: Deploy to Cloudflare

npx wrangler deploy --production

## Step 4: Verify deployment

curl https://your-subdomain.workers.dev/health
