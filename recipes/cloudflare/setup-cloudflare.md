---
name: Setup Cloudflare Environment
platforms: cloudflare
---

# Setup Cloudflare Environment

Initialize Cloudflare Workers project with necessary configuration.

## Step 1: Login to Cloudflare

npx wrangler login

## Step 2: Create new project

npx wrangler init my-project --type=webpack

## Step 3: Configure wrangler.toml

cat > wrangler.toml << 'WANGLER'
name = "my-project"
main = "src/index.ts"
compatibility_date = "2025-01-01"
[[routes]]
pattern = "myapp.example.com/*"
zone_name = "example.com"
WANGLER

## Step 4: Install dependencies

npm install @cloudflare/workers-types
