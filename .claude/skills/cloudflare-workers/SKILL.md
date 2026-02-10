---
name: cloudflare-workers
description: Manage Cloudflare Workers, KV, D1, R2, and secrets using Wrangler
---

# Cloudflare Workers Skill

## Workers

```bash
wrangler init [name]              # create new worker
wrangler dev                      # local development
wrangler deploy                   # deploy to production
wrangler tail                     # stream live logs
wrangler delete [name]            # delete worker
```

## KV Namespaces

```bash
wrangler kv namespace list
wrangler kv namespace create <name>
wrangler kv key put --namespace-id <id> <key> <value>
wrangler kv key get --namespace-id <id> <key>
wrangler kv key list --namespace-id <id>
wrangler kv key delete --namespace-id <id> <key>
```

## D1 Database

```bash
wrangler d1 list
wrangler d1 create <name>
wrangler d1 execute <db> --command "SELECT * FROM users"
wrangler d1 execute <db> --file schema.sql
wrangler d1 migrations create <db> <name>
wrangler d1 migrations apply <db>
```

## R2 Storage

```bash
wrangler r2 bucket list
wrangler r2 bucket create <name>
wrangler r2 object put <bucket>/<key> --file <path>
wrangler r2 object get <bucket>/<key>
```

## Secrets

```bash
wrangler secret put <name>        # set secret (prompts for value)
wrangler secret list              # list secrets
wrangler secret delete <name>     # remove secret
```

## Pages

```bash
wrangler pages project list
wrangler pages deploy <dir> --project-name <name>
```
