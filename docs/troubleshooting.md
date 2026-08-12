# Troubleshooting Guide

This guide covers common issues and their solutions when using Mekong CLI.

---

## Table of Contents

- [Quick Diagnosis](#quick-diagnosis)
- [Installation & Setup](#installation--setup)
- [LLM Configuration](#llm-configuration)
- [Command Issues](#command-issues)
- [Plugin System](#plugin-system)
- [Deployment](#deployment)
- [Database](#database)
- [Performance](#performance)
- [Authentication & Billing](#authentication--billing)
- [Vietnam Hub (VN HUB)](#vietnam-hub-vn-hub)
- [Logs & Debugging](#logs--debugging)

---

## Quick Diagnosis

Run these commands to diagnose issues:

```bash
# Check Mekong status
mekong status

# Check LLM connection
mekong status --check-llm

# List available commands
mekong help | head -20

# Check plugin system
mekong admin plugin list 2>/dev/null || echo "Plugin system not enabled"

# View recent logs
mekong logs --tail 100

# Validate configuration
mekong config validate 2>/dev/null || echo "Config validation not available"
```

---

## Installation & Setup

### "Command not found: mekong"

**Symptom:** Shell doesn't recognize `mekong` command.

**Check:**
```bash
which mekong
echo $PATH
```

**Fix:**
```bash
# Source the shell init script
source ~/mekong-cli/scripts/shell-init.sh

# Or add to your shell profile
echo "source ~/mekong-cli/scripts/shell-init.sh" >> ~/.zshrc  # or ~/.bashrc

# Restart terminal or source profile
source ~/.zshrc
```

### Python Dependencies Missing

**Symptom:** `ModuleNotFoundError` when running commands.

**Fix:**
```bash
# Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Node Dependencies Missing

**Symptom:** Cannot find module errors from CLI or SDK.

**Fix:**
```bash
cd ~/mekong-cli
pnpm install
```

---

## LLM Configuration

### "No LLM API key configured"

**Symptom:** Error about missing API key.

**Fix:**
```bash
# Choose one provider and set all three variables:
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# Add to ~/.zshrc for persistence
echo 'export LLM_BASE_URL=https://openrouter.ai/api/v1' >> ~/.zshrc
echo 'export LLM_API_KEY=sk-or-v1-yourkey' >> ~/.zshrc
echo 'export LLM_MODEL=anthropic/claude-sonnet-4' >> ~/.zshrc
```

### "Invalid API key" or "Authentication failed"

**Check:**
1. API key is correct (no typos)
2. API key has sufficient credits
3. Provider service is operational

**Fix:**
```bash
# Verify key works with curl
curl -H "Authorization: Bearer $LLM_API_KEY" \
  "$LLM_BASE_URL/models" | jq .
```

### LLM Timeout

**Symptom:** Requests time out after 30 seconds.

**Fix:**
```bash
# Increase timeout
export MEKONG_LLM_TIMEOUT=60

# Or use command flag
mekong cook "your goal" --timeout 120
```

### Using Local LLM (Ollama)

**Symptom:** Connection refused to localhost:11434.

**Fix:**
```bash
# Start Ollama
ollama serve &

# Pull model
ollama pull qwen2.5-coder

# Configure
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

---

## Command Issues

### "Command not found"

**Symptom:** `Error: Unknown command 'xxx'`

**Check:**
```bash
# List available commands
mekong help

# Search for similar commands
mekong search deploy
mekong search auth
```

**Fix:**
- Command name may be different - check the help output
- Plugin may not be loaded: `mekong admin plugin list`
- Command might be in a different layer: `mekong help --layer engineering`

### Command Fails with "Permission denied"

**Symptom:** Error about insufficient permissions.

**Fix:**
1. Check `.claude/settings.json` permissions
2. Run with explicit allow:
   ```bash
   mekong cook "goal" --allow Write,Bash
   ```
3. Add permission to settings.json:
   ```json
   {
     "permissions": {
       "allow": ["Write(./src/**)", "Bash(npm run:*)"]
     }
   }
   ```

### Command hangs or times out

**Symptom:** Command runs indefinitely or times out.

**Fix:**
```bash
# Increase timeout
mekong cook "goal" --timeout 300

# Break into smaller tasks
mekong cook "step 1 of 3: set up database"

# Check agent status
mekong status
mekong agent:tail --agent code-writer
```

---

## Plugin System

### Plugin Not Loading

**Symptom:** Plugin doesn't appear in `mekong plugin list`.

**Check:**
```bash
# Validate manifest
python3 -m scripts.plugin_validator validate ./plugin.json

# Check plugin logs
mekong admin plugin logs 2>&1 | grep -i error
```

**Common Issues:**
- Invalid JSON in `plugin.json` - run `python3 -m json.tool plugin.json`
- Missing `entrypoint` file
- `entrypoint` module doesn't exist or isn't importable
- Syntax errors in plugin code
- Missing `MekongPlugin` base class

### Plugin Command Not Found After Install

**Check:**
```bash
# Verify plugin is active
mekong plugin list

# Check plugin status
mekong plugin info <plugin-id>

# Re-scan plugins
mekong admin plugin scan
```

**Fix:**
1. Ensure `commands[].name` matches what you're typing
2. Plugin must be ACTIVE (not disabled)
3. Manifest `entrypoint` must register the command

### Permission Denied in Plugin

**Symptom:** "Error: Permission denied for network access"

**Fix:**
Add required permissions to `plugin.json`:
```json
{
  "permissions": {
    "network": ["https://api.example.com/*"],
    "file": ["read:./data", "write:./output"]
  }
}
```

Then reinstall:
```bash
mekong plugin install ./my-plugin --force
```

### Plugin Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'requests'`

**Fix:**
1. Add dependencies to `requirements.txt` in plugin directory:
   ```
   requests>=2.28.0
   stripe>=5.0.0
   ```
2. Reinstall plugin:
   ```bash
   mekong plugin install ./my-plugin --force
   ```

---

## Deployment

### Cloudflare Pages Deployment Fails

**Symptom:** Build fails or deployment returns error.

**Check:**
```bash
# Validate wrangler config
npx wrangler validate --config apps/dashboard/wrangler.toml

# Check wrangler version
wrangler --version  # Should be 3.x+
```

**Common Issues:**
- Missing secrets in GitHub Actions: Check repository Settings > Secrets
- Build fails due to missing env vars: Set `NEXT_PUBLIC_SUPABASE_URL`
- Account ID incorrect: Verify in Cloudflare Dashboard

### Worker Logs Not Showing

**Fix:**
```bash
# Tail live logs
wrangler tail mekong-api

# With environment
wrangler tail mekong-api --env staging
```

### Database Issues (D1)

**Symptom:** Database errors or migrations fail.

**Check:**
```bash
# List databases
wrangler d1 list

# Check database info
wrangler d1 info mekong-sessions

# Execute manual query
wrangler d1 execute mekong-sessions --command "SELECT * FROM sessions LIMIT 10"
```

**Fix:**
1. Ensure databases are created: `wrangler d1 create <name>`
2. Update `wrangler.toml` with correct database IDs
3. Run migrations: `npm run db:apply`

### KV Namespace Issues

**Symptom:** Rate limiting or caching not working.

**Fix:**
```bash
# Create KV namespaces
wrangler kv:namespace create RATE_LIMIT_KV
wrangler kv:namespace create CACHE_KV

# Update wrangler.toml with namespace IDs
```

---

## Database

### Database Connection Errors

**Check:**
```bash
# Verify database exists
ls -la data/  # or your database path

# Check connection string
echo $DATABASE_URL
```

**Fix:**
```bash
# For SQLite
export DATABASE_URL=sqlite:///data/app.db

# For PostgreSQL
export DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Migration Failures

**Symptom:** `mekong db:migrate` fails.

**Fix:**
```bash
# Check migration files exist
ls -la src/db/migrations/

# Run single migration with verbose output
mekong db:migrate --verbose

# Rollback last migration
mekong db:rollback
```

---

## Performance

### Slow Command Startup

**Symptom:** Commands take >10 seconds to start.

**Check:**
```bash
# Measure cold start
time mekong version
```

**Fix:**
1. Enable plugin caching:
   ```bash
   export MEKONG_PLUGIN_CACHE_ENABLED=true
   ```
2. Warm the cache:
   ```bash
   mekong admin plugin warm-cache
   ```
3. Profile slow plugins:
   ```bash
   mekong admin plugin profile
   ```

### High Memory Usage

**Check:**
```bash
# Monitor memory
ps aux | grep mekong
top -pid <mekong-pid>
```

**Fix:**
1. Reduce concurrent agents: `mekong cook "goal" --agents 2`
2. Disable unused plugins
3. Increase swap if needed

### LLM Rate Limiting

**Symptom:** "Rate limit exceeded" errors.

**Fix:**
```bash
# Add delay between requests
export MEKONG_LLM_RATE_LIMIT_DELAY=1

# Or upgrade your API plan with the provider
```

---

## Authentication & Billing

### "Insufficient credits" Error

**Symptom:** Command blocked due to zero balance.

**Check:**
```bash
# Check balance
mekong billing/balance

# Check usage
mekong billing/usage --period month
```

**Fix:**
1. Top up credits: `mekong billing/topup --amount 100`
2. Upgrade plan: `mekong billing/activate --plan growth`
3. Check Polar/Stripe subscription status

### Webhook Failures (Polar/Stripe)

**Symptom:** Webhook events not being processed.

**Check:**
```bash
# View webhook logs
tail -f ~/.mekong/logs/webhook.log

# Test webhook endpoint
curl -X POST https://your-domain.com/webhooks/polar \
  -H "Webhook-Signature: test" \
  -d '{"event": "test"}'
```

**Fix:**
1. Verify webhook secret is correct
2. Ensure endpoint is accessible (not behind auth)
3. Check webhook retry policy in dashboard

### JWT Token Errors

**Symptom:** "Invalid token" or "Token expired".

**Fix:**
```bash
# Refresh token
mekong auth refresh

# Or re-login
mekong auth logout
mekong auth login
```

---

## Vietnam Hub (VN HUB)

### Zalo OA Integration Fails

**Symptom:** Zalo API returns errors.

**Check:**
```bash
# Verify credentials
echo $ZALO_ACCESS_TOKEN
echo $ZALO_APP_ID

# Test connection
mekong zalo/verify --access-token $ZALO_ACCESS_TOKEN
```

**Fix:**
1. Ensure access token is valid (not expired)
2. Check app is in production mode (not development)
3. Verify OA is properly configured in Zalo dashboard

### Vietnamese LLM Not Responding

**Symptom:** VN-specific commands fail.

**Fix:**
```bash
# Check Rapid-MLX is running
curl http://localhost:8001/v1/models

# Start if not running
brew services start rapid-mlx
rapid-mlx serve qwen3.6-35b --port 8001
```

---

## Logs & Debugging

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG
export MEKONG_DEBUG=1

# Run command with verbose output
mekong cook "goal" --verbose
```

### View Plugin Logs

```bash
# All plugin logs
mekong admin plugin logs

# Specific plugin
mekong admin plugin logs <plugin-id>

# Follow logs
mekong admin plugin logs --follow

# With timestamps
mekong admin plugin logs --timestamps
```

### Gateway Logs

```bash
# API gateway logs
tail -f ~/.mekong/logs/gateway.log

# Agent logs
tail -f ~/.mekong/logs/agent.log

# Error logs
tail -f ~/.mekong/logs/errors.log
```

### Core Debug Locations

| Log | Path |
|-----|------|
| Gateway | `~/.mekong/logs/gateway.log` |
| Agents | `~/.mekong/logs/agent.log` |
| Errors | `~/.mekong/logs/errors.log` |
| Usage | `~/.mekong/usage_events.jsonl` |
| Billing | `~/.mekong/billing.log` |
| Plugin Migration | `~/.mekong/logs/plugin-migration.log` |

---

## Common Error Messages

### "Plugin validation failed: dangerous import"

**Cause:** Plugin uses blocked imports like `subprocess`, `eval`, `exec`.

**Fix:** Remove dangerous patterns or request exemption.

### "Command recursive: self-reference detected"

**Cause:** Command tries to invoke itself.

**Fix:** Check command implementation for circular calls.

### "MCU balance exceeded"

**Cause:** Not enough credits.

**Fix:** Top up or wait for reset (monthly).

### "Database is locked"

**Cause:** Another process holds the database lock.

**Fix:**
```bash
# Find and kill lock holder
lsof | grep .mekong/data.db

# Or use WAL mode (recommended)
export MEKONG_DB_WAL_MODE=1
```

### "Port already in use"

**Cause:** Another process on the port.

**Fix:**
```bash
# Find process on port
lsof -i :8000

# Kill it or change port
export MEKONG_PORT=8001
```

---

## Recovery Procedures

### Reset Mekong to Clean State

```bash
# Backup first
cp -r ~/.mekong ~/.mekong.backup-$(date +%Y%m%d)

# Remove state (preserves config, clears state)
rm -rf ~/.mekong/tasks/
rm -rf ~/.mekong/cache/
rm -rf ~/.mekong/plugins/installed/

# Restart
mekong platform restart gateway
```

### Rollback Plugin

```bash
# Disable problematic plugin
mekong admin plugin disable <plugin-id>

# Or remove completely
mekong admin plugin uninstall <plugin-id>

# Restore from backup
cp -r ~/.mekong/plugins.backup/<plugin-id> ~/.mekong/plugins/installed/
mekong admin plugin scan
```

### Clear Corrupted Cache

```bash
rm -rf ~/.mekong/cache/
rm -rf ~/.mekong/__pycache__/
mekong admin cache clear
```

---

## Getting Help

1. **Check this guide** - Most issues covered here
2. **Run diagnostic**: `mekong diagnose` (if available)
3. **View logs** - See [Logs & Debugging](#logs--debugging)
4. **Community** - Discord: `#support`
5. **GitHub Issues** - [Create an issue](https://github.com/longtho638-jpg/mekong-cli/issues/new)

When asking for help, include:
- Mekong version: `mekong version`
- OS and shell
- Error message (full output)
- Steps to reproduce
- Relevant logs

---

## Still Stuck?

If your issue isn't covered here:

1. Search existing [GitHub Issues](https://github.com/longtho638-jpg/mekong-cli/issues)
2. Check the [discussions](https://github.com/longtho638-jpg/mekong-cli/discussions)
3. Join our [Discord server](https://discord.gg/mekong)
4. Create a new issue with diagnostic information
