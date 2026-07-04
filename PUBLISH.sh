#!/bin/bash
# PUBLISH.sh — Sanitize mekong-cli for public distribution
# Usage: cd ~/mekong-cli && bash PUBLISH.sh
# Output: ~/mekong-cli-public/

set -euo pipefail

SRC="${1:-$(pwd)}"
DEST="${2:-$HOME/mekong-cli-public}"

if [ ! -f "$SRC/package.json" ] || ! grep -q "mekong-cli" "$SRC/package.json" 2>/dev/null; then
    echo "ERROR: Run from mekong-cli root or pass path as arg"
    exit 1
fi

echo "🔒 Sanitizing $SRC → $DEST"
mkdir -p "$DEST"

# 1. Copy everything first
echo "📋 Copying source..."
cp -R "$SRC"/. "$DEST"/

# 2. Remove excluded directories
echo "🗑️  Removing internal directories..."
EXCLUDE_DIRS=(
    ".credentials" "config" ".mekong" ".agents" "data" "models"
    ".venv-seed" ".pytest_cache" ".ruff_cache" ".husky" ".ci"
    ".astro" ".turbo" "__pycache__" ".opencode" "node_modules"
    ".git" ".archive" ".gemini"
    "plans" "observability"
)
for d in "${EXCLUDE_DIRS[@]}"; do
    rm -rf "$DEST/$d" 2>/dev/null && echo "  removed: $d/"
done

# 3. Remove excluded files
echo "🗑️  Removing internal files..."
EXCLUDE_FILES=(
    # Internal docs
    "STRATEGY.md" "GO_LIVE_PLAYBOOK.md" "GO_LIVE_REPORT.md"
    "BACKEND_REFACTORING_REPORT.md" "PHASE2_REFACTORING_SUMMARY.md"
    "PHASE4_INTEGRATION_COMPLETE.md" "final-security-compliance-report.md"
    "phase-4-security-completion-report.md" "integration_test_report.json"
    "integration_test_report.md" "TEST_INFRA.md" "TEST_READY.md"
    "OPUS_HANDOFF_PROMPT.md" "ORIGINAL_REQUEST.md" "PROJECT.md"
    "AGY.md" "ANTIGRAVITY.md" "IDEA_AUTOPILOT.md"
    "HARNESS.md" "AGENTS.md" "ARCHITECTURE.md" "QUICKSTART.md"
    "repomix-output.xml" "usage_2026-03-09_current.json"
    "content_tweets_agencyos_20260117.txt" "demo_script.md"
    "run_validation.log" "run_validation.sh" "verify_brand.py"
    "fix_indent.py" "fix_security.py" "apply_all_fixes.py"
    "apply_all_fixes_v2.py" "reapply_fixes.py" "m1-cooler.sh"
    "factory-loop.sh" "docker-compose.posthog.yml"
    "docker-compose.seed.yml" "requirements.seed.txt"
    "conftest.py" "tsc-errors.txt" "ecosystem.social.cjs"
    ".gitignore-extra" "openclaw.json" ".openclaw-config.json"
    ".openclaw.pid" "eslint.config.mjs"
    # Lock files (dev only)
    "poetry.lock" "package-lock.json" "pnpm-lock.yaml"
)
for f in "${EXCLUDE_FILES[@]}"; do
    rm -f "$DEST/$f" 2>/dev/null && echo "  removed: $f"
done

# 4. Sanitize .claude/skills — keep core 50
echo "✂️  Trimming skills to core set..."
KEEP_SKILLS=(
    # Core workflow
    "bootstrap" "cook" "plan" "scout" "debug" "fix" "test"
    "code-review" "review" "ship" "git" "brainstorm"
    # Frontend/Backend
    "frontend-development" "frontend-design" "backend-development"
    "nextjs-best-practices" "react-patterns" "tailwind-patterns"
    # Data/Infra
    "databases" "deploy" "devops" "docker-expert"
    "aws-serverless" "security" "security-scan"
    # AI/Agents
    "context-engineering" "prompt-engineering" "rag-implementation"
    "ai-agents-architecture" "multi-agent-orchestration"
    "use-mcp" "mcp-builder"
    # Quality
    "sequential-thinking" "problem-solving" "docs"
    "docs-seeker" "research" "preview"
    # Productivity
    "worktree" "vercel-debug" "playwright"
    "testing-patterns" "tdd-workflow"
    # Design
    "ui-styling" "ui-ux-pro-max" "design"
    # Content
    "copywriting" "marketing" "seo-fundamentals"
    # Utilities
    "repomix" "excalidraw" "tech-graph"
    "markdown-novel-viewer" "show-off" "web-frameworks"
    # Other core
    "better-auth" "payment-integration" "billing"
    "api-monetization" "subscription-saas-ops"
    "monitoring-observability" "legal-compliance"
    "privacy-compliance" "web-design-guidelines"
)
SKILLS_DIR="$DEST/.claude/skills"
if [ -d "$SKILLS_DIR" ]; then
    for skill_dir in "$SKILLS_DIR"/*/; do
        skill_name=$(basename "$skill_dir")
        keep=false
        for k in "${KEEP_SKILLS[@]}"; do
            if [ "$skill_name" = "$k" ]; then
                keep=true
                break
            fi
        done
        if [ "$keep" = false ]; then
            rm -rf "$skill_dir"
            echo "  removed skill: $skill_name"
        fi
    done
fi

# 5. Sanitize .claude/commands — keep core 40
echo "✂️  Trimming commands to core set..."
KEEP_CMDS=(
    "ask" "bootstrap" "brainstorm" "code" "cook" "debug" "design"
    "docs" "fix" "git" "idea" "integrate" "journal" "plan"
    "preview" "remember" "review" "save" "scout" "skill"
    "test" "worktree" "ship" "delegate" "approve" "recover"
    "sync" "bootstrap-auto" "cook-auto" "code-auto"
    "fix-fast" "fix-hard" "fix-parallel" "fix-test"
    "plan-fast" "plan-hard" "plan-parallel"
    "scout-ext" "review-codebase" "review-codebase-parallel"
    "docs-update" "docs-init" "docs-summarize"
    "marketing" "marketing-seo" "marketing-copy"
    "marketing-growth" "marketing-ads" "marketing-cro"
    "me-status" "quality-gate" "build-check" "code-audit"
)
CMDS_DIR="$DEST/.claude/commands"
if [ -d "$CMDS_DIR" ]; then
    for cmd_file in "$CMDS_DIR"/*.md; do
        [ -f "$cmd_file" ] || continue
        cmd_name=$(basename "$cmd_file" .md)
        keep=false
        for k in "${KEEP_CMDS[@]}"; do
            if [ "$cmd_name" = "$k" ]; then
                keep=true
                break
            fi
        done
        if [ "$keep" = false ]; then
            rm -f "$cmd_file"
            echo "  removed command: $cmd_name"
        fi
    done
fi

# 6. Sanitize .claude/hooks — keep safety hooks only
echo "✂️  Trimming hooks to safety set..."
KEEP_HOOKS=(
    "pre-push-check" "claude-code-review" "claude-deploy-prep"
    "post-write-check" "error-recovery" "privacy-block"
    "pre-tool-use-guard" "simplify-gate"
    "workflow-artifact-gate" "stop-checkpoint"
)
HOOKS_DIR="$DEST/.claude/hooks"
if [ -d "$HOOKS_DIR" ]; then
    for hook_file in "$HOOKS_DIR"/*; do
        [ -f "$hook_file" ] || continue
        hook_name=$(basename "$hook_file" .sh .cjs)
        keep=false
        for k in "${KEEP_HOOKS[@]}"; do
            if [ "$hook_name" = "$k" ]; then
                keep=true
                break
            fi
        done
        if [ "$keep" = false ]; then
            rm -f "$hook_file"
            echo "  removed hook: $hook_name"
        fi
    done
fi

# 7. Strip secrets from code files
echo "🔑 Scanning for secrets..."
SECRET_PATTERNS=(
    "HERMES_API_KEY" "ANTHROPIC_API_KEY" "OPENAI_API_KEY"
    "POLAR_API_KEY" "STRIPE_SECRET" "STRIPE_KEY"
    "password" "PASSWORD" "secret_key" "SECRET_KEY"
    "api_key.*=.*['\"]" "token.*=.*['\"]sk-"
    "claude.zunef.com" "zunef.com"
)
found_secrets=0
for pattern in "${SECRET_PATTERNS[@]}"; do
    matches=$(grep -rl "$pattern" "$DEST" --include="*.py" --include="*.ts" --include="*.js" --include="*.sh" --include="*.json" --include="*.md" --include="*.yaml" --include="*.yml" 2>/dev/null | grep -v "node_modules" | grep -v ".git" | grep -v "__pycache__" | head -20)
    if [ -n "$matches" ]; then
        echo "  ⚠️  Potential secret pattern '$pattern' in:"
        echo "$matches" | sed 's/^/    /'
        found_secrets=$((found_secrets + 1))
    fi
done

if [ "$found_secrets" -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: $found_secrets secret patterns found!"
    echo "   Review the files above and manually fix before publishing."
    echo "   Continue anyway? (y/N)"
    read -r confirm
    if [ "${confirm,,}" != "y" ]; then
        echo "Aborted. Fix secrets first."
        exit 1
    fi
else
    echo "✅ No secrets detected"
fi

# 8. Create public README
echo "📝 Creating public README..."
cat > "$DEST/README.md" << 'PUBLICREADME'
# Mekong IDE — The One-Person Company Platform

> **One person. 10 business layers. $49/mo.**
> Replace a 50-person team with autonomous agents.

## Quick Start

```bash
curl -fsSL https://www.mekongmind.com/install.sh | bash
```

## What is Mekong IDE?

The platform that enables the **one-person billion-dollar company**. 10 business layers — Founder, Business, Product, Engineering, Ops, Studio, CTO, PM, Dev, Worker — all operated by agents.

## What's Included

- **490+ commands** across 10 business layers
- **58 unified agents** with department mapping
- **Claude Code integration** with custom skills + hooks
- **Harness engineering** — context budget, guardrails, delegation
- **SOPs** — Standard Operating Procedures per department
- **Dashboard** — Web UI for monitoring
- **CF Deployment** — Cloudflare Pages + Workers + KV

## Architecture

```
User → CLI → Agent Registry → Claude Code → SOPs → State
```

## Requirements

- Node.js 18+ + pnpm
- Python 3.11+ + poetry
- Docker (optional)
- Claude Code CLI
- Ollama (optional, for local LLM)

## Install

```bash
# One-liner
curl -fsSL https://www.mekongmind.com/install.sh | bash

# Or manual
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
pnpm install
pip install -r requirements.txt
```

## Usage

```bash
me --help                    # Main CLI
me idea "build API"          # Create goal
me step 1                    # Execute step 1
me goal show                 # Show progress
me sops list                 # List SOPs
```

## Pricing

| Plan | Price | Credits |
|------|-------|---------|
| Starter | $49/mo | 200 |
| Growth | $149/mo | 1,000 |
| Pro | $499/mo | 5,000 |

[Subscribe](https://buy.polar.sh/polar_cl_apvIt00Pf7vw2GGX0PW7tWfNjSiwaTRUl0YzO3YqVhA)

## Links

- [Website](https://mekongmind.com)
- [IDE](https://ide.mekongmind.com)
- [Guides](https://mekongmind.com/guides/)

## License

MIT
PUBLICREADME

# 9. Update install.sh for public
echo "📝 Updating install.sh..."
if [ -f "$SRC/scripts/install.sh" ]; then
    cp "$SRC/scripts/install.sh" "$DEST/install.sh"
elif [ -f "$SRC/install.sh" ]; then
    cp "$SRC/install.sh" "$DEST/install.sh"
fi

# 10. Create .gitignore for public
cat > "$DEST/.gitignore" << 'GITIGNORE'
# Dependencies
node_modules/
.pnp
.pnp.js
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/

# Build
.next/
.out/
dist/
build/
.open-next/
.wrangler/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Env
.env
.env.local
.env.*.local

# Internal (never commit)
plans/
data/
.mekong/
.credentials/
config/
.agents/
observability/
.ci/
.husky/
.astro/
.turbo/
.opencode/
.archive/
.gemini/

# Logs
*.log
logs/

# Test internals
repomix-output.xml
usage_*.json
conftest.py
tsc-errors.txt
GITIGNORE

# 11. Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ Sanitization complete!"
echo "📁 Output: $DEST"
echo "📊 Size: $(du -sh "$DEST" | cut -f1)"
echo "📁 Files: $(find "$DEST" -type f | wc -l)"
echo ""
echo "Next steps:"
echo "  cd $DEST"
echo "  git init && git add . && git commit -m 'feat: initial public release'"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"
echo ""
echo "⚠️  Review secret scan results above before pushing!"
