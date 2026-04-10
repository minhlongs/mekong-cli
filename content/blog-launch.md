# Why we built one IDE instead of 13 products

We started with 13 product ideas. AI trading bot. AI content studio. AI compliance checker. AI legal counsel. Thirteen different landing pages, thirteen different billing flows, thirteen different onboarding sequences.

Then we asked: what do all 13 have in common?

The answer: the same 290 operational commands, the same AI classifier, the same LLM router, the same credit system. The "products" were identical except for which department's commands they highlighted.

So we stopped building 13 products and started selling one: **Mekong IDE**.

## What Mekong IDE actually is

An AI operating system with 22 departments built in. Finance, marketing, sales, engineering, legal, compliance, HR, design — every function a business needs, powered by AI agents that know how to execute.

You tell it what you want:

```
"Create a quarterly financial report for Q1 2026"
```

It classifies (CFO department), matches the right command (finance-budget-plan), routes to the best LLM, and delivers structured output. One credit deducted.

## The Office 365 model

Microsoft doesn't sell Word separately from Excel separately from PowerPoint. You buy Office 365 and get everything.

Mekong IDE works the same way:

- **$49/month** — all 22 departments, 200 credits
- **$149/month** — all 22 departments, 1,000 credits
- **$499/month** — all 22 departments, 5,000 credits

No feature gates. No department lock-outs. Credits determine how much you run, not what you can access.

## Run it on your own hardware

The entire system runs on a MacBook Pro with Ollama. No cloud required. No API costs. Your data never leaves your machine.

```bash
git clone https://github.com/longtho638-jpg/mekong-cli
ollama pull qwen2.5-coder:7b
uvicorn src.gateway:app --port 8000
```

22 departments. 290 commands. Zero cloud cost.

## What's next

We're publishing Mekong IDE as an OpenClaw skill (351K GitHub stars) and a ClaudeKit operations kit. If you use Claude Code, you can install our 290 commands today and start running business operations from your terminal.

Subscribe: https://polar.sh/longtho638-jpg
Docs: https://agencyos.network
