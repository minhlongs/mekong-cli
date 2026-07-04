---
name: Configure R2 Storage
platforms: cloudflare
---

# Configure R2 Storage

Set up R2 bucket for object storage in Cloudflare Workers.

## Step 1: Create R2 bucket via dashboard

# Go to Cloudflare Dashboard → R2 → Create Bucket
# Name: my-bucket

## Step 2: Add binding to wrangler.toml

[[r2_buckets]]
binding = "BUCKET"
bucket_name = "my-bucket"

## Step 3: Test R2 access from code

npx wrangler dev
