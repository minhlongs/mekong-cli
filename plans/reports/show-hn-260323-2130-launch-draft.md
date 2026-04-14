# Show HN Post Draft

## Title (80 char max)

**Show HN: Mekong CLI -- AI-operated business platform with 300+ commands**

Alt titles:
- Show HN: Mekong CLI -- One command runs multi-agent workflows for your whole business
- Show HN: Mekong CLI -- 300+ AI commands for engineering, sales, finance, ops

---

## Body

Hi HN,

I built Mekong CLI, an open-source platform where you describe a business goal in natural language and AI agents plan, execute, and verify the work.

**What it does:**

- 300+ commands across 5 business layers (founder, business, product, engineering, ops)
- PEV engine: Plan -> Execute -> Verify with self-healing on failure
- Works with any OpenAI-compatible LLM (3 env vars: BASE_URL, API_KEY, MODEL)
- $0 infrastructure: deploys on Cloudflare free tier (Workers + D1 + Pages)
- DAG workflows: commands compose into parallel multi-agent pipelines

**Examples:**

```
mekong cook "Create a SaaS landing page with Stripe"    # Engineering
mekong founder:raise "Series A for AI platform"          # Founder (8 agents parallel)
mekong marketing "Launch campaign for new product"       # Business
mekong audit "Full security review"                      # Ops
```

**Technical details:**

- Python PEV engine + TypeScript SDK (npm packages published)
- 388 typed JSON contracts (every command has input/output schema)
- 5,713 tests (1,263 TypeScript + 4,450 Python)
- Universal LLM: OpenRouter, Anthropic, OpenAI, DeepSeek, Ollama, MLX
- Built on top of Claude Code CLI but works with any LLM backend

**Try it:**

```
git clone --depth 1 https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli && source scripts/shell-init.sh
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=your-key
export LLM_MODEL=anthropic/claude-sonnet-4
mekong cook "Create a Python REST API with auth"
```

Or just the SDK: `npm install @mekongcli/openclaw-engine`

GitHub: https://github.com/longtho638-jpg/mekong-cli

I built this because I was running a venture studio and realized 80% of the work across all portfolio companies followed the same patterns -- the same planning, building, testing, deploying, marketing cycles. So I encoded those patterns into typed contracts that any LLM can execute.

Would love feedback on the command structure and whether the 5-layer business abstraction makes sense to you.

---

## Posting Checklist

- [ ] README is compelling and accurate
- [ ] QUICKSTART.md works end-to-end
- [ ] CONTRIBUTING.md has correct paths
- [ ] npm packages installable (`npm install @mekongcli/openclaw-engine`)
- [ ] CI is GREEN
- [ ] No secrets in repo
- [ ] Demo GIF in README (optional but high-impact)
- [ ] Post on weekday 9-11am ET for best visibility
- [ ] Reply to early comments within 1 hour
