# 🏆 Everything Claude Code — 謀攻篇 Battle-Tested CC CLI Config Pack

> Source: github.com/affaan-m/everything-claude-code
> Assessed: 2026-02-18 | Status: CRITICAL KEEP — P1
> Action: Install plugin + AgentShield scan + Continuous Learning

## What
- Complete CC CLI config collection (42K+ stars!)
- Anthropic Hackathon Winner, 10+ months production use
- Agents, skills, hooks, commands, rules, MCPs all included

## 3 CRITICAL Tools

### 1. AgentShield — Security Auditor
```bash
npx ecc-agentshield scan              # Quick scan
npx ecc-agentshield scan --opus       # 3x Opus red-team/blue-team
npx ecc-agentshield scan --fix        # Auto-fix
```
- 912 tests, 98% coverage, 102 static analysis rules
- Scans: CLAUDE.md, settings.json, MCP, hooks, agents, skills
- Red-team (attack) + Blue-team (defend) + Auditor pipeline

### 2. Continuous Learning v2
```bash
/instinct-status    # Show learned patterns
/instinct-import    # Import from others
/instinct-export    # Share instincts
/evolve             # Cluster instincts → skills
```
- Auto-learns patterns from your usage
- Compounds intelligence over time

### 3. Token Optimization
- Strategic Compact: /compact at logical breakpoints
- MCP Limit: Max 10 MCPs, 80 tools active
- CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50 (not 95% default)
- Agent Teams: parallel is expensive, use subagents for sequential

## Integration Plan
1. Install as CC CLI plugin
2. Run AgentShield scan on Tôm Hùm configs
3. Enable Continuous Learning v2
4. Apply token optimization settings to AG Proxy
5. Use Skill Creator to generate skills from mekong-cli git history

## Binh Pháp
- 謀攻篇: "Biết trước sẽ thắng" — security scan + learning
- 虛實篇: Token optimization = context savings
- 軍形篇: AgentShield = fortress defense for agent configs

## Priority: P1 — proven, massive community, critical security + learning tools
