# Open-Core Gravitational Architecture Research Report
**Mekong CLI: Building a "Solar System" Business Model**

*Date: 2026-03-23*
*Agent: Researcher*
*Status: Complete*

---

## Executive Summary

This research identifies **5 proven architectural patterns** that create "gravitational pull" — where the core platform FORCES the community to contribute back to get domain-specific features working. Successful open-core companies ($10M-$400M+ ARR) share these patterns:

1. **Plugin/Provider System** — Core platform = Sun, community integrations = Planets
2. **Schema-Driven Development** — Community code must follow core types & contracts
3. **Execution-Based Pricing** — Monetize *usage* of plugins, not plugins themselves
4. **Fair-Code Licensing** — Prevent cloud providers from reselling, preserve upstream value
5. **Monorepo + Governance** — Single source of truth, clear ownership, seamless contributions

**Bottom line:** If architecture forces divergence = forks. If architecture rewards convergence = ecosystem.

---

## Part 1: Open-Core Success Stories ($10M+ ARR)

### 1.1 Grafana Labs ($400M+ ARR) — LGTM Stack Gravity

**Pattern:** Open-source observability core + enterprise cloud hosting

- **Gravitational Pull:** Grafana dashboards pull metrics from Loki, Tempo, Prometheus
- **Community Lock-in:** Users build custom queries, dashboards, alerts — can't migrate easily
- **Revenue Model:** Free OSS + Grafana Cloud ($50-5000+/mo) + Enterprise features
- **Result:** 96% retention on paying customers, $400M ARR in 2024

**Key Insight:** LGTM stack (Loki, Grafana, Tempo, Mimir) creates *dependency chains*. You need:
- Grafana for visualization (free OSS)
- But want Loki/Tempo for better data (cloud or self-hosted managed)
- Then need Mimir for long-term storage
- Eventually upgrade to Enterprise for RBAC/audit/compliance

Source: [Grafana Labs Announces Updates to Kubernetes Monitoring Solution](https://grafana.com/about/press/2024/03/12/grafana-labs-announces-updates-to-kubernetes-monitoring-solution-open-source-innovations-and-findings-from-2024-observability-survey/)

### 1.2 Supabase ($70M ARR 2025) — Firebase Alternative

**Pattern:** Open-source PostgreSQL wrapper + managed cloud

- **Gravitational Pull:** You start with free `supabase-js` SDK, then need auth/storage/functions
- **Core-to-Cloud Gravity:** Self-hosted Supabase is possible but requires DevOps; cloud is $25-599/mo
- **Revenue Mix:** 70% cloud subscriptions, 20% enterprise, 10% other
- **Result:** $2B valuation (2025), $70M ARR after 5 years

**Lesson for Mekong:** Supabase succeeded because PostgreSQL is *too powerful to avoid*. Every feature build needs it. Same pattern: make the core *so essential* that alternatives are worse than paying.

Sources: [Supabase revenue, valuation & funding](https://sacra.com/c/supabase/), [Supabase 2026 Company Profile](https://pitchbook.com/profiles/company/437773-51)

### 1.3 n8n ($40M ARR, $2.5B valuation 2025) — Workflow Automation

**Pattern:** Open-source workflow engine + execution credits

- **Fair-Code License:** Sustainable Use License prevents cloud reselling
- **Community Nodes:** 2.2k+ community-built integrations (vs 400 native ones)
- **Execution-Based Pricing:** Pay per workflow run, not per feature
- **Result:** 3,000+ enterprise customers, 55% cloud revenue + 30% enterprise + 15% OEM

**Critical Pattern:**
```
Community writes nodes (integrations) → n8n executes them → customers pay per execution
Community wins: their nodes are discovered, used by thousands
n8n wins: execution fees, customer lock-in on cloud
Customers win: cheap custom integrations from community
```

**Lesson:** Monetizing execution (not features) incentivizes community contribution. Community nodes = n8n's competitive advantage.

Sources: [Inside n8n: How a Fair-Code, Open-Source Platform Leads AI-Powered Workflow Automation](https://medium.com/@takafumi.endo/inside-n8n-how-a-fair-code-open-source-platform-leads-ai-powered-workflow-automation-e8128890d496), [n8n revenue, valuation & funding](https://sacra.com/c/n8n/)

### 1.4 Kubernetes ($88k+ contributors, 8000+ companies)

**Pattern:** Plugin system that BECOMES the platform

- **Convention-Based Discovery:** Any executable `kubectl-*` becomes a plugin
- **SIG Structure:** Special Interest Groups own domains (networking, storage, scheduling)
- **Governance:** Large contributors embedded in decision-making
- **Result:** 96% enterprise adoption, 2nd-largest OSS project globally

**Gravitational Architecture:**
```
kubectl core = very minimal (ETCD API, scheduler, kubelet)
Kubernetes ecosystem = 88k contributors adding: CNI, CSI, operators, CRDs
Users can't avoid the ecosystem: they NEED networking, storage, monitoring
Ecosystem = now *more* important than core
```

**Lesson:** Design core to be *extensible by necessity*, not convenience.

Sources: [Digital transformation driven by community: Kubernetes as example](https://www.cncf.io/blog/2025/01/30/digital-transformation-driven-by-community-kubernetes-as-example/), [k0s in 2025: A year of community growth](https://www.cncf.io/blog/2026/01/26/k0s-in-2025-a-year-of-community-growth-governance-and-kubernetes-innovation/)

### 1.5 Hugging Face ($2M+ models ecosystem)

**Pattern:** Hub is the platform, community models are the gravity

- **Community Lock-in:** You publish your model on HF → gets discovered → becomes your portfolio
- **GitHub Integration:** Star count on HF ≈ academic/industry credibility
- **Downloads:** NVIDIA emerged as strongest contributor to HF ecosystem
- **Result:** 2M models + 500k datasets + 1M demos in single place

**Lesson:** Make contribution to your platform = career signal. HF succeeds because publishing on HF is *valuable to authors*, not just useful to users.

Sources: [State of Open Source on Hugging Face: Spring 2026](https://huggingface.co/blog/huggingface/state-of-os-hf-spring-2026), [Anatomy of a Machine Learning Ecosystem: 2 Million Models on Hugging Face](https://arxiv.org/html/2508.06811v1)

### 1.6 LangChain ($1.25B valuation 2025) — Framework → Observability

**Pattern:** Open-source framework with paid observability layer

- **Split Model:** LangChain (free, MIT) + LangSmith (paid, $39-1000+/mo per seat)
- **Observability Lock-in:** Once you use LangChain, you want visibility into traces → LangSmith
- **Pricing:** Free tier (5k traces/mo), then $39/seat
- **Result:** $125M Series B (2025), $1.25B valuation, 40% revenue growth

**Critical Insight:** LangChain didn't force observability into core. Instead:
- Core stays lightweight, free, MIT-licensed
- Paid service solves a *new* problem (observability)
- Users adopt both organically (core → observability → LangSmith)

Sources: [LangSmith: AI Agent & LLM Observability Platform](https://www.langchain.com/langsmith/observability), [Introducing End-to-End OpenTelemetry Support in LangSmith](https://blog.langchain.com/end-to-end-opentelemetry-langsmith/)

---

## Part 2: Gravitational Architecture Patterns

### Pattern #1: Plugin/Provider System (Mandatory)

**Definition:** Core platform exposes hooks/extension points. Community builds plugins that extend functionality WITHOUT modifying core.

#### Examples:

**Terraform Providers (1000+ community providers)**
- Terraform core = minimal (plan, apply, state)
- Providers = anyone can write (Go binary)
- Community writes AWS, Azure, Kubernetes, custom providers
- Gravity: You need providers → you contribute or pay for managed ones
- Source: [Top Terraform Alternatives And Competitors To Know](https://www.cloudzero.com/blog/terraform-alternatives/)

**kubectl Plugins (100s of plugins via Krew)**
- kubectl core = minimal (apply, get, describe)
- Plugins = any executable prefixed `kubectl-`
- Convention-based discovery, no registration needed
- Gravity: Operators need plugins for production (monitoring, debugging, security)
- Source: [Extend kubectl with plugins](https://kubernetes.io/docs/tasks/extend-kubectl/kubectl-plugins/)

**WordPress Plugins (58k+ plugins)**
- WordPress core = lightweight CMS
- Plugins = extend via hooks (filter, action)
- All GPL-licensed, creates ecosystem lock-in
- Gravity: Every business need requires plugins
- Source: [The WordPress Ecosystem](https://learn.wordpress.org/lesson/the-wordpress-ecosystem-2/)

#### For Mekong CLI:

**Current State:** 542 skills, 342+ commands, 410 contracts — already plugin-like

**Upgrade Path:**
```yaml
Tier 1 (Current): Commands are hardcoded in .claude/commands/
Tier 2 (Upgrade): Community-contributed skills in ~/.mekong/community-skills/
Tier 3 (Gravity): Community skills MUST follow MCP-like schema
Tier 4 (Ecosystem): Marketplace rates skills by adoption, quality, updates
```

**Implementation:**
```bash
# Directory structure for community plugins
~/.mekong/skills/community/
├── terraform-cost-analyzer/  # Community contributor
│   ├── skill.yaml           # Schema
│   ├── plugin.py
│   └── tests/
├── github-pr-analyzer/
├── linkedin-recruiter/
└── SKILL_SCHEMA.json        # Define contracts
```

**Lock-in Mechanism:** Once community publishes skill on marketplace, they're invested. They market it, improve it, fix bugs. Forking Mekong = losing their skill audience.

---

### Pattern #2: Schema-Driven Development (Critical)

**Definition:** All contributions (skills, commands, contracts) follow strict TypeScript/JSON schemas. Contributors must conform to your data model.

#### Why This Creates Gravity:

**Type Safety Across Ecosystem:**
```typescript
// mekong-core/types/skill.ts (exported, immutable)
export interface Skill {
  id: string;
  name: string;
  inputs: Record<string, InputParam>;   // STRICT schema
  outputs: Record<string, OutputParam>;
  version: string;
  license: "MIT" | "Apache-2.0" | "AGPL-3.0";
  requires: string[];  // dependency graph
}

// Community contributor writes skill that MUST match this
// They can't fork and change the schema — it won't work!
// The only way forward: contribute the schema change + get it approved
```

**Benefits:**
- **Type checking across ecosystem** — TypeScript knows all skill inputs/outputs
- **Automatic discovery** — CLI can introspect any skill
- **Zero compatibility risk** — schema validation at runtime
- **Hard to fork** — custom schema = broken ecosystem

#### Examples in the Wild:

**Kubernetes CRDs (Custom Resource Definitions)**
- Every custom resource MUST match OpenAPI schema
- Community extends K8s via CRDs (not by forking)
- Schema validation prevents incompatibility

**MCP (Model Context Protocol) — Anthropic's 2024 Launch**
- Open standard for AI agent tools
- Every MCP server MUST implement JSON-RPC schema
- Adopted by OpenAI, Google DeepMind, Microsoft
- **Key:** Community *can't* deviate from schema; they contribute via the standard
- Result: Thousands of MCP servers in first 2 months
- Sources: [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol), [A Year of MCP: From Internal Experiment to Industry Standard](https://www.pento.ai/blog/a-year-of-mcp-2025-review)

**n8n Node Schema**
```typescript
export abstract class INodeType {
  description: INodeTypeDescription;  // STRICT schema
  execute(...): Promise<INodeExecutionData[][]>;
}
// Community writes nodes that MUST implement this interface
// Can't deviate; forces upstream contribution to change standard
```

---

### Pattern #3: Execution-Based Pricing (Revenue Engine)

**Definition:** Monetize *when* plugins run, not *which* plugins exist.

#### Why This Works:

**Aligns Incentives:**
- Community writes plugins → more plugins = more executions → more revenue
- Cloud provider needs plugins → pays for executions
- No zero-sum game: growth in ecosystem = growth in revenue

#### n8n Model ($40M ARR):
```
Community writes 2.2k+ nodes (integrations)
User runs workflow with 5 nodes × 1,000 times/month = 5,000 executions
n8n charges: $0.001-0.01 per execution (simplified)
User pays: $5-50/month
Community gets: visibility, adoption, portfolio
n8n gets: $50/mo × 3,000 customers = $150k/mo from execution fees alone
```

#### For Mekong CLI:

**Current:** MCU-based billing (credits per plan, unclear execution model)

**Upgrade to Execution-Based:**
```yaml
Pricing Model:
  Free: 50 skill executions/month (soft limit)
  Pro ($49/mo): 10,000 executions/month + parallel execution
  Enterprise: Unlimited + priority queue

Execution = any skill run, including community-authored
Community wins: their skills earn adoption metrics
Mekong wins: growth in skill adoption = growth in execution volume
```

**Implementation:**
```python
# src/billing/execution_tracker.py
async def track_execution(skill_id: str, user_id: str, status: str):
    """Track every skill execution for billing"""
    execution = Execution(
        skill_id=skill_id,          # terraform-cost-analyzer
        user_id=user_id,
        community_author=get_author(skill_id),
        status=status,              # success, failure, timeout
        duration_ms=duration,
        timestamp=now()
    )
    await execution.save()

    # Increment user's execution counter for billing
    await user.increment_executions(1)

    # Track community author stats (for marketplace ranking)
    await skill.increment_total_runs(1)
```

---

### Pattern #4: Fair-Code Licensing (Strategic Moat)

**Definition:** Prevent cloud providers from reselling your code under a different brand while preserving open-source spirit.

#### The Pattern:

**Traditional Open-Source (MIT/Apache):**
```
Any company can:
- Take source code
- Offer as managed service (charge customers)
- No obligation to contribute back
- You lose the ecosystem (users go to cloud provider instead)

Examples of loss:
- Elasticsearch → AWS OpenSearch (AWS stopped contributing)
- Terraform → cloud providers managed Terraform services (BSL license introduced)
```

**Fair-Code (Sustainable Use License):**
```
Anyone can:
- Use code for internal use (free)
- Self-host (free)
- Modify for own use (free)

NO ONE can:
- Offer as a cloud service (unless contribute back)
- Resell the service (unless contribute back)

Result:
- Ecosystem preserved (users stay with original platform)
- Community contribution incentivized (only way to commercialize)
- Forks fail (divergence costs more than upstream contribution)
```

#### n8n's Success with SUL:

> "Sustainable Use License prevents hyperscale cloud providers from offering competing services using n8n's code without contributing back to the ecosystem."

Result: AWS, Azure, Google Cloud avoid competing with n8n. n8n keeps ecosystem.

#### For Mekong CLI:

**Current License:** BSL 1.1 (changes to MIT 2028-03-13)

**Recommendation:**
```markdown
# Proposed Timeline

2026-2027: Keep BSL 1.1 (prevents early forks)
2028: Switch to AGPL-3.0 OR Sustainable Use License
      (NOT MIT — MIT is how you lose the ecosystem)

AGPL-3.0: Anyone can fork, but modifications MUST be open-sourced
SUL: Anyone can fork, but can't commercialize without upstream contribution

Either preserves the ecosystem better than MIT.
```

Sources: [The Open Source License Change Pattern](https://www.softwareseni.com/the-open-source-license-change-pattern-mongodb-to-redis-timeline-2018-to-2026-and-what-comes-next), [Why AWS Supports Valkey](https://aws.amazon.com/blogs/opensource/why-aws-supports-valkey/), [One year ago Redis changed its license – and lost most of its external contributors](https://devclass.com/2025/04/01/one-year-ago-redis-changed-its-license-and-lost-most-of-its-external-contributors/)

---

### Pattern #5: Monorepo + Governance (Operational)

**Definition:** Single source of truth for core + ecosystem. Clear ownership prevents fork drift.

#### Structure:

```
mekong-cli/  (monorepo = single repo)
├── src/             # Core engine (you own)
├── .claude/skills/  # Official skills (you maintain)
├── .claude/commands/  # Official commands (you own + community contributes)
├── community/       # Community-contributed (clear CODEOWNERS)
│   ├── MAINTAINERS.md
│   └── skills/
│       ├── terraform-cost-analyzer/
│       │   ├── MAINTAINERS  # Clear owner (GitHub username)
│       │   ├── skill.yaml
│       │   └── tests/
│       └── github-pr-analyzer/
├── factory/contracts/  # Shared data models (core owns)
├── docs/            # Shared docs (both maintain)
└── GOVERNANCE.md    # Clear rules for contributing
```

#### Why Monorepo Prevents Forks:

**Git Contributor Experience:**
```
Fork (separate repo):
- Your changes drift immediately
- After 6 months: rebasing is painful
- After 12 months: you might not bother merging
- Result: your custom skill is stuck at old version

Monorepo contribution (PR in main repo):
- You add your skill to community/
- It's tested, reviewed, merged
- Future Mekong updates apply to your code
- No divergence
- No rebase pain
- You stay upstream

Psychology: Contributing to monorepo is EASIER than maintaining a fork.
```

#### Governance Example (Kubernetes):

```markdown
# GOVERNANCE.md

## Contributing a Skill

1. Fork repo
2. Add your skill to community/skills/{name}/
3. Follow SKILL_SCHEMA.json
4. Add yourself to MAINTAINERS
5. Submit PR

## Code Review SLA
- Core team: 48h review
- Community: any approval + 1 core maintainer = merge

## Becoming a Maintainer
- 3+ merged PRs
- Regular responses to issues in your skill
- Community votes (50% of maintainers)

## Escalation
- If code review stalled > 1 week → ping on Discord
- If decision disputed → steering committee votes
```

**Result:** Clear expectations = fewer forks.

Sources: [Monorepo governance: module best practices and code ownership](https://dev.to/kodus/monorepo-governance-module-best-practices-and-code-ownership-4o10), [Building Leadership in an Open Source Community](https://www.linuxfoundation.org/resources/open-source-guides/building-leadership-in-an-open-source-community)

---

## Part 3: Anti-Patterns to Avoid

### Anti-Pattern #1: Ambiguous Licensing (Kills Ecosystem)

**What Happened:**
- Redis → BSD → SSPL (March 2024)
- Community backlash immediately → forked as Valkey (Linux Foundation)
- Within 12 months: 83% of large Redis users adopted Valkey
- Result: Redis lost most external contributors

**Lesson:** License *stability* matters more than permissiveness. If you change licenses, you signal:
- "We don't respect the community's implicit contract"
- "Forking is safer than staying"

**For Mekong:** Commit to AGPL or SUL *now*. Don't wait until 2028 to surprise the community.

Source: [One year ago Redis changed its license – and lost most of its external contributors](https://devclass.com/2025/04/01/one-year-ago-redis-changed-its-license-and-lost-most-of-its-external-contributors/)

### Anti-Pattern #2: Centralized Plugin Distribution (WordPress FAIR)

**What Happened:**
- WordPress ecosystem grew to 58k+ plugins
- But wordpress.org (plugin registry) is privately owned, single point of failure
- Community concern: what if Automattic shuts it down?
- Result: Community launched FAIR (Fair And Independent Repositories) to decentralize

**Lesson:** Distribute control of plugin marketplace. Don't let it become a chokepoint.

**For Mekong:**
```yaml
Plugin Distribution Strategy:
  Stage 1 (Current): Official marketplace at mekong.sh/skills
  Stage 2 (Future): Allow mirrors (GitHub Releases, npm, etc.)
  Stage 3 (Ideal): Decentralized registry (DNS-based, IPFS backup)

This prevents: "What if Mekong.sh goes down?"
```

Source: [Introducing FAIR: A federated approach to strengthen the WordPress ecosystem](https://allthingsopen.org/articles/fair-federated-approach-wordpress-ecosystem)

### Anti-Pattern #3: Forcing Contribution (Kills Adoption)

**What Happened:**
- Some projects *require* contributing back to use advanced features
- Result: Users fork instead of paying / contributing
- Community perceives it as **gatekeeping**

**Lesson:** Make contribution *rewarding*, not *mandatory*.

**For Mekong:**
```yaml
DON'T DO:
  "To use 5+ skills in parallel, you MUST contribute a skill"

DO THIS INSTEAD:
  "Use 5+ skills in parallel ($50/mo plan)"
  "Plus: Community contributors get free Plan for their authored skills"

Incentive = free tier for authors, not forced contribution
```

---

## Part 4: Architectural Recommendations for Mekong CLI

### 4.1 Immediate (Q2 2026): Plugin System Upgrade

**Goal:** Make community contributions *the default path* for feature extensions.

```yaml
Changes:
  1. Move .claude/commands/ to be auto-discoverable from ~/.mekong/
  2. Create schema validation for all skills/commands
  3. Add skill versioning (semver)
  4. Create simple installer: mekong skill:install terraform-cost-analyzer

Result: Community can publish skills without git PR
        Skills version independently of core
        Clear upgrade path
```

**File Structure:**
```bash
~/.mekong/
├── config.yaml
├── skills/
│   ├── official/        # Your maintained skills
│   │   ├── translate/
│   │   └── summarize/
│   └── community/       # Community-authored
│       ├── terraform-cost-analyzer/
│       ├── github-pr-reviewer/
│       └── linkedin-recruiter/
└── commands/
    └── similar structure
```

### 4.2 Short-Term (Q3 2026): Schema Standardization

**Goal:** Make it impossible to fork Mekong without losing the ecosystem.

```typescript
// mekong-core/types/skill-schema.ts (published + immutable)
export interface MekongSkill {
  // Metadata
  id: string;                    // terraform-cost-analyzer (must be unique)
  name: string;                  // Human-readable name
  version: string;               // semver (1.0.0)
  author: string;                // GitHub username
  license: "MIT" | "Apache-2.0" | "AGPL-3.0" | "BSL-1.1";

  // Definition
  description: string;
  inputs: Record<string, InputParameter>;
  outputs: Record<string, OutputParameter>;

  // Dependencies
  requires: {
    mekong: string;              // ">=1.0.0,<2.0.0"
    skills: string[];            // ["terraform", "aws-sdk"]
  };

  // Governance
  maintainer: GitHubUser;
  verified: boolean;             // by core team
  published_at: Date;

  // Marketplace
  stars: number;                 // User rating
  downloads: number;
  latest_update: Date;
}
```

**Benefit:** Any community skill MUST match this schema. You can't fork Mekong and change the schema — it breaks compatibility.

### 4.3 Medium-Term (Q4 2026): Marketplace + Execution Tracking

**Goal:** Monetize execution while celebrating community authors.

```yaml
Marketplace Features:
  1. Skill leaderboard (by downloads, rating, updates)
  2. Author profiles (skills, contributions, followers)
  3. Skill trending (new, popular, trending-this-week)
  4. Execution stats (public: "terraform-cost-analyzer was used 10k times this week")

Execution Tracking:
  1. Every skill run = 1 execution credit
  2. User quota: Free 50/mo, Pro 10k/mo, Enterprise unlimited
  3. API endpoint: /api/executions (for billing + analytics)

Revenue:
  - Free: 50 executions/month
  - Pro: $49/mo for 10k executions
  - Enterprise: $499+/mo unlimited

Community Benefit:
  - Skill authors see adoption metrics (public dashboard)
  - Popular skills = visibility = career signal
  - Option: Free Pro tier for community authors (to reward)
```

### 4.4 Long-Term (2027+): Governance Formalization

**Goal:** Community-driven steering committee, not benevolent dictator.

```markdown
# GOVERNANCE.md (Model)

## Structure
- Core Team (3-5): Technical decisions, breaking changes
- Maintainers (10-20): Community contributors with commit rights
- Contributors (100+): Community members with merged PRs

## Decision Making
- Feature proposals: GitHub Discussions
- Minor changes: Any maintainer approval + 1 core team member
- Breaking changes: Core team consensus
- License/governance changes: Community vote (50%+ of maintainers)

## Becoming a Maintainer
- 5+ merged PRs across core + community skills
- Active in issues (answering questions)
- Community nominates → core team votes

## Escalation
- Disputed technical decision → Core team decides
- Disputed governance decision → Public vote (all contributors)
- Maintainer abuse → Community can revoke commit rights
```

**Why This Works:** Kubernetes, Linux, WordPress all follow this model. It signals *sustainability* to users and contributors.

---

## Part 5: Competitive Advantages This Creates

### 5.1 Gravitational Pull: The Math

**Scenario A: Without Gravitational Architecture**
```
Month 1: You build 10 features yourself
Month 2: Users ask for 20 more features → You burn out
Month 3: Users fork to add features → Ecosystem splits
Month 6: Forks stabilize → Your platform loses mindshare
Result: Death spiral (fewer contributors → worse features → more forks)
```

**Scenario B: With Gravitational Architecture**
```
Month 1: You build 5 core features + plugin system
         Community builds 10 community skills
Month 2: You maintain core + 5 official skills
         Community maintains 20 new community skills
         Total: 35 features (vs 20 if you built alone)
Month 3: Momentum: 50+ community skills
         Users see: rich ecosystem, vibrant community
         Forks fail: ecosystem = the platform
Month 6: 500+ community skills published
         Your job: maintain 5-10 core features + platform health
         Revenue: from execution fees (not support)
Result: Sustainable growth (compounding community contributions)
```

### 5.2 Sustainable Revenue, Not Burnout

**Old Model (Mekong + 50 skills built in-house):**
```
Revenue: Free OSS + optional enterprise support
Challenge: Can't afford to hire 50 engineers to build/maintain all skills
Result: Underfunded, outdated, burnout
```

**New Model (Mekong core + community authors for 500+ skills):**
```
Revenue: Execution-based pricing
         Free tier: 50 executions/month
         Pro: $49/mo × 1000 users = $50k/month
         Enterprise: $499+/mo × 100 customers = $50k/month
Total: $100k+/month from execution fees alone

Your team:
- Core platform: 5 engineers
- Community relations: 2 engineers
- Infrastructure: 3 engineers
Total: 10 engineers running $100k/mo platform
vs 50+ engineers to build features

ROI: 5-10x better than feature-building
```

### 5.3 Strategic Moat: Ecosystem Switching Cost

**Why Users Stay:**
```
User has 200 community skills running their workflows
User considers competing platform (e.g., Zapier, Make)

Switching cost:
- Rewrite 200 skills in competitor's schema: $500k+
- Retrain 50 users on new system: $50k+
- Recreate workflows: $100k+
Total: $650k+ switching cost

Result: User is locked in, but *by choice* (ecosystem value), not *by force*
This is the healthiest lock-in: value-driven, not contractual
```

---

## Part 6: Implementation Roadmap (2026-2027)

### Phase 1: Foundation (Q2 2026)
- [ ] Define SKILL_SCHEMA.json (locked, immutable)
- [ ] Publish skill schema as npm package (@mekong/core-types)
- [ ] Create skill validator (CLI tool)
- [ ] Add skill versioning (semver)
- [ ] Create mekong skill:publish CLI command

### Phase 2: Marketplace (Q3 2026)
- [ ] Build skill marketplace website (mekong.sh/marketplace)
- [ ] Skill leaderboard, search, filtering
- [ ] Author profiles + verification badges
- [ ] Integration with GitHub Releases for publishing
- [ ] Execution metrics dashboard (public)

### Phase 3: Monetization (Q4 2026)
- [ ] Implement execution tracking in core engine
- [ ] Billing system for execution quotas
- [ ] Free tier: 50 executions/month
- [ ] Pro tier: $49/month (10k executions)
- [ ] Enterprise tier: $499+/month (unlimited)

### Phase 4: Governance (2027)
- [ ] Publish GOVERNANCE.md
- [ ] Elect initial Maintainers (5-10 community members)
- [ ] Create Steering Committee
- [ ] Quarterly public votes on breaking changes
- [ ] Linux Foundation alignment (optional)

---

## Unresolved Questions

1. **Fair-Code vs AGPL vs MIT transition (2028)?**
   - Current: BSL 1.1
   - Recommendation: AGPL-3.0 (safest for ecosystem)
   - Question: Does your business model allow AGPL downstream?
   - Action: Legal review before 2027

2. **Community skill revenue sharing?**
   - Option A: Authors get free Pro tier (suggested)
   - Option B: Revenue share (e.g., 10-20% of execution fees to author)
   - Question: Sustainable at scale? (If 500 authors, each needs $X/month)
   - Action: Financial model by Q4 2026

3. **Competing community skills (multiple terraform-cost analyzers)?**
   - Current: No policy
   - Risk: Users confused, spam authors publish low-quality skills
   - Action: Proposal: Top-rated skill gets featured, others discoverable
           Maintainers curate quality, not enforce monopoly

4. **Marketplace governance: who approves skills?**
   - Option A: Automatic (publish = instant visibility)
   - Option B: Core team reviews (slower, curated)
   - Option C: Community votes (transparent, slower)
   - Recommendation: Start with B (core review), move to C as community grows

5. **Skill versioning backwards compatibility?**
   - If Mekong 2.0 changes SKILL_SCHEMA, what happens to v1.0 skills?
   - Recommendation: Deprecation period (e.g., "v1 skills supported until 2027")
   - Action: Draft deprecation policy before major version

6. **Self-hosting marketplace skills?**
   - If user self-hosts Mekong, can they use marketplace skills?
   - Current answer: Unknown
   - Recommendation: Yes, but only discover from official registry
   - Action: Architecture decision needed

---

## References

**Open-Core Business Models:**
- [Grafana Labs Announces Updates to Kubernetes Monitoring Solution](https://grafana.com/about/press/2024/03/12/grafana-labs-announces-updates-to-kubernetes-monitoring-solution-open-source-innovations-and-findings-from-2024-observability-survey/)
- [Supabase revenue, valuation & funding](https://sacra.com/c/supabase/)
- [Inside n8n: How a Fair-Code, Open-Source Platform Leads AI-Powered Workflow Automation](https://medium.com/@takafumi.endo/inside-n8n-how-a-fair-code-open-source-platform-leads-ai-powered-workflow-automation-e8128890d496)
- [n8n revenue, valuation & funding](https://sacra.com/c/n8n/)

**Kubernetes Ecosystem:**
- [Digital transformation driven by community: Kubernetes as example](https://www.cncf.io/blog/2025/01/30/digital-transformation-driven-by-community-kubernetes-as-example/)
- [k0s in 2025: A year of community growth, governance, and Kubernetes innovation](https://www.cncf.io/blog/2026/01/26/k0s-in-2025-a-year-of-community-growth-governance-and-kubernetes-innovation/)

**Plugin Architectures:**
- [Extend kubectl with plugins](https://kubernetes.io/docs/tasks/extend-kubectl/kubectl-plugins/)
- [Terraform Alternatives](https://www.cloudzero.com/blog/terraform-alternatives/)
- [The WordPress Ecosystem](https://learn.wordpress.org/lesson/the-wordpress-ecosystem-2/)

**ML Communities:**
- [State of Open Source on Hugging Face: Spring 2026](https://huggingface.co/blog/huggingface/state-of-os-hf-spring-2026)
- [Anatomy of a Machine Learning Ecosystem: 2 Million Models on Hugging Face](https://arxiv.org/html/2508.06811v1)

**License Changes & Forks:**
- [The Open Source License Change Pattern](https://www.softwareseni.com/the-open-source-license-change-pattern-mongodb-to-redis-timeline-2018-to-2026-and-what-comes-next)
- [Why AWS Supports Valkey](https://aws.amazon.com/blogs/opensource/why-aws-supports-valkey/)
- [One year ago Redis changed its license – and lost most of its external contributors](https://devclass.com/2025/04/01/one-year-ago-redis-changed-its-license-and-lost-most-of-its-external-contributors/)

**MCP (Anthropic's Standard):**
- [Introducing the Model Context Protocol](https://www.anthropic.com/news/model-context-protocol)
- [A Year of MCP: From Internal Experiment to Industry Standard](https://www.pento.ai/blog/a-year-of-mcp-2025-review)

**Governance & Contribution:**
- [Monorepo governance: module best practices and code ownership](https://dev.to/kodus/monorepo-governance-module-best-practices-and-code-ownership-4o10)
- [Building Leadership in an Open Source Community](https://www.linuxfoundation.org/resources/open-source-guides/building-leadership-in-an-open-source-community)
- [Introducing FAIR: A federated approach to strengthen the WordPress ecosystem](https://allthingsopen.org/articles/fair-federated-approach-wordpress-ecosystem)

**Fork Divergence:**
- [Stop Forking Around - The Hidden Dangers of "Fork Drift" in Open Source Adoption](https://preset.io/blog/stop-forking-around-the-hidden-dangers-of-fork-drift-in-open-source-adoption/)
- [No Forking Way: Our 6 Rules For Open Source Code Management](https://engineering.salesforce.com/no-forking-way-dc5fa842649b/)

---

## Conclusion

**The Core Insight:**

Successful open-core companies don't ask "how do we grow faster than competitors?" They ask "how do we make the community *invest in our platform*?"

The answer: Design the architecture so that **forks are more expensive than upstream contribution**.

This requires:
1. **Plugin System** → Community extends core without forking
2. **Schema-Driven Development** → Custom schemas = broken compatibility
3. **Execution-Based Pricing** → Ecosystem growth = revenue growth
4. **Fair-Code Licensing** → Cloud resellers contribute back or fail
5. **Monorepo + Governance** → Clearer path to contribute than to fork

Mekong CLI already has the building blocks (542 skills, 410 contracts, plugin-like architecture). The upgrade: make those blocks *irresistible* to contribute back to.

**Bottom line:** Turn users into authors. Turn authors into maintainers. Turn maintainers into stakeholders.

That's the "gravitational pull."

---

*Report prepared: 2026-03-23*
*Sources verified: 25+ authoritative sources*
*Implementation complexity: Medium (4-6 months for full rollout)*
*Recommended start: Q2 2026*
