#!/bin/bash
# raas-sales-gen.sh - Generate RaaS sales proposals from template
# Usage: raas-sales-gen.sh --template <config.yaml> --output <output.md>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEMPLATE_FILE=""
OUTPUT_FILE=""
HELP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --template)
            TEMPLATE_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Show help
if [ "$HELP" = true ] || [ -z "$TEMPLATE_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     RaaS Sales Proposal Generator                        ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Generate customized Revenue-as-a-Service sales proposals"
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 --template <config.yaml> --output <output.md>"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --template, -t    Path to YAML configuration file"
    echo "  --output, -o      Path for output markdown file"
    echo "  --help, -h        Show this help message"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo "  $0 --template ~/mekong-cli/templates/client-acme.yaml \\"
    echo "      --output ~/sales/pipeline/acme-proposal-2026-03-19.md"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  1. Copy template: cp ~/mekong-cli/templates/raas-demo-config.yaml ~/clients/acme.yaml"
    echo "  2. Edit config:   vim ~/clients/acme.yaml"
    echo "  3. Generate:      $0 --template ~/clients/acme.yaml --output ~/sales/acme.md"
    echo ""
    exit 0
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}Error: Template file not found: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
if [ ! -d "$OUTPUT_DIR" ]; then
    echo -e "${YELLOW}Creating output directory: $OUTPUT_DIR${NC}"
    mkdir -p "$OUTPUT_DIR"
fi

# Get current date
CURRENT_DATE=$(date +"%Y-%m-%d")
FORMATTED_DATE=$(date +"%B %d, %Y")

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Generating RaaS Sales Proposal                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓${NC} Template: $TEMPLATE_FILE"
echo -e "${GREEN}✓${NC} Output:   $OUTPUT_FILE"
echo -e "${GREEN}✓${NC} Date:     $FORMATTED_DATE"
echo ""

# Parse YAML config (simple bash parser for our specific format)
parse_yaml_value() {
    local key=$1
    local file=$2
    grep "^  $key:" "$file" 2>/dev/null | sed "s/^  $key: *//" | sed 's/^"\(.*\)"$/\1/' | head -1
}

parse_yaml_nested() {
    local parent=$1
    local key=$2
    local file=$3
    # Parse nested YAML with 2-space indentation and strip comments
    awk "/^$parent:/{found=1} found && /^  $key:/{print; exit}" "$file" | sed "s/^  $key: *//" | sed 's/^"\(.*\)"$/\1/' | sed 's/  #.*//'
}

# Extract values from config
CLIENT_NAME=$(parse_yaml_nested "client" "name" "$TEMPLATE_FILE")
CLIENT_COMPANY=$(parse_yaml_nested "client" "company" "$TEMPLATE_FILE")
CLIENT_INDUSTRY=$(parse_yaml_nested "client" "industry" "$TEMPLATE_FILE")
RECOMMENDED_TIER=$(parse_yaml_nested "client" "recommended_tier" "$TEMPLATE_FILE")

# ROI values
HOURLY_RATE=$(parse_yaml_nested "roi_projections" "current_hourly_rate" "$TEMPLATE_FILE")
MONTHLY_HOURS=$(parse_yaml_nested "roi_projections" "monthly_hours_automated" "$TEMPLATE_FILE")
MONTHLY_VALUE=$(parse_yaml_nested "roi_projections" "monthly_value_generated" "$TEMPLATE_FILE")
NET_ROI=$(parse_yaml_nested "roi_projections" "net_monthly_roi" "$TEMPLATE_FILE")

# Use defaults if not found
CLIENT_NAME=${CLIENT_NAME:-"[Client Name]"}
CLIENT_COMPANY=${CLIENT_COMPANY:-"[Company Name]"}
CLIENT_INDUSTRY=${CLIENT_INDUSTRY:-"[Industry]"}
RECOMMENDED_TIER=${RECOMMENDED_TIER:-"pro"}
HOURLY_RATE=${HOURLY_RATE:-"200"}
MONTHLY_HOURS=${MONTHLY_HOURS:-"62"}
MONTHLY_VALUE=${MONTHLY_VALUE:-"9,300"}
NET_ROI=${NET_ROI:-"9,151"}

echo -e "${GREEN}✓${NC} Client: $CLIENT_NAME ($CLIENT_COMPANY)"
echo -e "${GREEN}✓${NC} Industry: $CLIENT_INDUSTRY"
echo -e "${GREEN}✓${NC} Recommended Tier: $RECOMMENDED_TIER"
echo ""

# Generate proposal
echo -e "${YELLOW}Generating proposal...${NC}"

cat > "$OUTPUT_FILE" << EOF
# RaaS Sales Proposal — Revenue-as-a-Service

> **Transform your agency from hourly billing to outcome-based revenue.**
> *Track every dollar. Measure every outcome. Prove ROI in real-time.*

**Prepared for:** $CLIENT_NAME
**Company:** $CLIENT_COMPANY
**Industry:** $CLIENT_INDUSTRY
**Date:** $FORMATTED_DATE
**Prepared by:** Binh Phap Venture Studio

---

## Executive Summary

**The Problem:** Hourly billing is broken. Clients hate unpredictable costs. Agencies hate being capped by human capacity.

**The Solution:** RaaS (Revenue-as-a-Service) sells outcomes, not hours. AI agents execute development missions autonomously. You scale without hiring.

**The ROI:** Pro tier customers average **62x ROI** — \$9,151 net value/month on \$149 investment.

---

## Client-Specific Analysis

### Current State Assessment

Based on your profile as **$CLIENT_INDUSTRY**, here are the typical challenges:

| Challenge | Impact | RaaS Solution |
|-----------|--------|---------------|
| **Unpredictable Costs** | Budget overruns, client friction | Fixed monthly pricing |
| **Capacity Constraints** | Turning down revenue | 24/7 AI agent execution |
| **Hiring Challenges** | 3-6 month ramp, expensive | Instant scale |
| **Tech Debt** | Velocity decreases over time | Auto-elimination |

### Your Projected ROI

Based on industry benchmarks for **$CLIENT_INDUSTRY**:

\`\`\`
Current Development Costs:
├─ Hourly Rate:     \$${HOURLY_RATE}/hour
├─ Monthly Hours:   ~${MONTHLY_HOURS} hours (estimated)
└─ Monthly Cost:    \$${MONTHLY_VALUE}

RaaS Pro Tier:
├─ Subscription:    \$149/month
├─ Value Generated: \$${MONTHLY_VALUE}
└─ Net ROI:         \$${NET_ROI}/month (62x return)
\`\`\`

---

## The Business Case

### Why Hourly Billing Fails Everyone

| Clients Hate | Agencies Hate |
|--------------|---------------|
| Unpredictable costs | Revenue capped by hours |
| Paying for inefficiency | Penalized for speed |
| Scope negotiations | Feast-or-famine cash flow |

**Result:** Adversarial relationship. Everyone loses.

### Why RaaS Wins

| Old Model (Hourly) | New Model (RaaS) |
|--------------------|------------------|
| Bill for hours | Bill for outcomes |
| Client manages tasks | AI agents execute |
| Revenue = hours × rate | Revenue = missions × tier |
| Scale = hire more | Scale = deploy more agents |

**Bottom Line:** Clients get predictability. Agencies get scalability. Everyone wins.

---

## Recommended Tier: **Pro** — \$149/mo ⭐

**Perfect for:** $CLIENT_INDUSTRY scaling operations

| | |
|---|---|
| **Credits** | 1,000/month (5x Starter) |
| **Projects** | 10 max |
| **Commands** | All basic + \`/deploy\`, \`/audit\`, \`/security\`, \`/kanban\` |
| **LLM** | Premium (Claude 4.6, Gemini 1.5 Pro) |
| **Support** | Priority, 12hr |
| **ROI Dashboard** | ✅ Live tracking |
| **API Access** | ✅ Programmatic missions |
| **ROI** | Automate 50-75 hrs/month |

**Best For $CLIENT_COMPANY:**
- Full sprint automation
- CI/CD pipeline management
- Multi-repo refactoring
- Agent team orchestration
- Automated code reviews

---

## ROI Tracking — The Heart of RaaS

### Your Custom ROI Dashboard

\`\`\`
┌─────────────────────────────────────────────────────────┐
│  RaaS ROI Dashboard — $CLIENT_COMPANY                   │
├─────────────────────────────────────────────────────────┤
│  Missions Completed:     [Live tracking]                │
│  Credits Used:           [Real-time]                    │
│  Est. Hours Saved:       ${MONTHLY_HOURS} hrs  →  \$${MONTHLY_VALUE} value       │
│  Tech Debt Fixed:        [Auto-counted]                 │
│  Production Deploys:     [Auto-tracked]                 │
│  Success Rate:           [Quality metrics]              │
│  Avg. Completion Time:   ~4 minutes                     │
└─────────────────────────────────────────────────────────┘
\`\`\`

### ROI Formula

\`\`\`
Your Monthly ROI = (Hours Saved × Agency Rate) - RaaS Subscription

For $CLIENT_COMPANY:
= (${MONTHLY_HOURS} hrs × \$${HOURLY_RATE}/hr) - \$149
= \$${MONTHLY_VALUE} - \$149
= \$${NET_ROI} net value/month
= 62x ROI
\`\`\`

---

## What Gets Automated for $CLIENT_COMPANY

Every mission passes Binh Phap quality gates:

\`\`\`
Quality Gate          Target    Verification
─────────────────────────────────────────────────────────
Tech Debt             0 TODO    grep -r "TODO\\|FIXME" src
Type Safety           0 any     grep -r ": any" src
Clean Code            0 console grep -r "console\\." src
Tests                 100% pass npm test
Performance           Build<10s time npm run build
\`\`\`

**Automation Areas:**
- ✅ Code features (write, test, deploy)
- ✅ Bug fixes (auto-detect, fix, verify)
- ✅ CI/CD pipelines (build, deploy, monitor)
- ✅ Security audits (scan, fix, report)
- ✅ Tech debt removal (0 tolerance)
- ✅ Data pipelines & reports
- ✅ Agent team orchestration
- ✅ Documentation generation

---

## Demo Mission Suggestions

Here's what we recommend automating first:

### Mission 1: Sprint Automation
**Credits:** 10 | **Complexity:** Multi-Agent

\`\`\`
Description: Automate a full development sprint with AI agents
Steps:
1. /plan create sprint backlog from tickets
2. /cook implement feature A
3. /cook implement feature B
4. /test run full test suite
5. /review code quality audit
6. /deploy ship to staging
\`\`\`

### Mission 2: Tech Debt Elimination
**Credits:** 5 | **Complexity:** Complex

\`\`\`
Description: Scan and fix all technical debt
Steps:
1. /scout find all TODOs, console.logs, any types
2. /fix remove TODOs with proper implementations
3. /fix replace console.log with structured logging
4. /fix replace :any with proper TypeScript types
5. /test verify all tests pass
6. /review confirm 0 tech debt
\`\`\`

### Mission 3: CI/CD Pipeline Setup
**Credits:** 5 | **Complexity:** Complex

\`\`\`
Description: Configure automated testing and deployment
Steps:
1. /cook create GitHub Actions workflow
2. /cook add linting, type checking, tests
3. /cook configure Vercel deployment
4. /test verify pipeline passes
5. /deploy test production deploy
\`\`\`

---

## Competitive Comparison

### vs Traditional Agency

| Metric | Traditional Agency | RaaS Pro |
|--------|-------------------|----------|
| **Monthly Cost** | \$${MONTHLY_VALUE} (20hrs × \$${HOURLY_RATE}) | \$149 |
| **Turnaround** | Days-weeks | Minutes-hours |
| **Availability** | Business hours | 24/7 |
| **Tech Debt** | Accumulates | Auto-eliminated |
| **ROI Tracking** | Manual estimates | Live dashboard |

**Annual Savings: \$${MONTHLY_VALUE}/mo × 12 - \$149 × 12 = \$46,212/year**

### vs Building In-House

| Cost Component | In-House | RaaS |
|----------------|----------|------|
| Developer Salary | \$150K-250K/yr | \$1,788/yr |
| Benefits/Overhead | 30% of salary | \$0 |
| Recruiting | \$20K-50K/hire | \$0 |
| Management Time | 10-20 hrs/week | Autonomous |

---

## Implementation Timeline

\`\`\`
Week 1: Foundation
├─ Day 1-2: Account setup, team onboarding
├─ Day 3-4: First 10 missions (quick wins)
└─ Day 5: Week 1 ROI review

Week 2: Expansion
├─ Identify high-value automation opportunities
├─ Train team on mission specification
└─ Establish quality baselines

Week 3: Optimization
├─ Analyze usage patterns
├─ Optimize mission templates
└─ Scale to 50+ missions/week

Week 4: Full Operations
├─ 24/7 autonomous operations
├─ Monthly ROI: \$${NET_ROI}+ net value
└─ Expansion planning
\`\`\`

---

## Next Steps

### Immediate Actions

| # | Action | Timeline | Owner |
|---|--------|----------|-------|
| 1 | **Book Live Demo** | This week | $CLIENT_NAME |
| 2 | **Start 14-Day Trial** | After demo | $CLIENT_COMPANY |
| 3 | **First Mission** | Day 1 of trial | Technical lead |
| 4 | **ROI Review** | Day 14 | Both parties |

### Contact Information

| Channel | Details |
|---------|---------|
| **Demo Booking** | [agencyos.network/demo](https://agencyos.network/demo) |
| **Start Trial** | [agencyos.network/pricing](https://agencyos.network/pricing) |
| **Sales Email** | sales@agencyos.network |
| **Documentation** | [agencyos.network/docs](https://agencyos.network/docs) |

---

## FAQ

**Q: What happens if we run out of credits?**

A: Pro tier includes 1,000 credits/month. If you exceed, you can purchase top-ups at \$0.25/credit or upgrade to Enterprise for unlimited.

**Q: Can we pause the subscription?**

A: Yes, pause anytime. Projects remain accessible, missions queue until resume.

**Q: What if a mission fails?**

A: Credits automatically refunded. Full audit log shows failure reason and recovery steps.

**Q: Is our code safe?**

A: Yes. Enterprise tier includes private knowledge vault — data never leaves your boundary. SOC2 compliance available.

**Q: What LLMs do you support?**

A: All major providers via Antigravity Proxy: Claude 4.6, Gemini 1.5 Pro, Qwen 3.5+, and local Ollama models.

---

## Terms Summary

| Term | Details |
|------|---------|
| **Trial Period** | 14 days, full Pro access |
| **Billing Cycle** | Monthly or annual (2 months free) |
| **Cancellation** | Anytime, no penalty |
| **Data Ownership** | Customer retains all IP |
| **Support** | Email (Starter), Priority 12hr (Pro), 4hr SLA (Ent) |

---

> **"The supreme art of war is to subdue the enemy without fighting."**
> — 孫子兵法 (Sun Tzu)

**RaaS: Win by automating the grind. Focus your team on strategy.**

---

© 2026 Binh Phap Venture Studio
*Generated by RaaS Sales Generator v1.0*
EOF

echo -e "${GREEN}✓${NC} Proposal generated successfully!"
echo ""
echo -e "${BLUE}Output: ${NC}$OUTPUT_FILE"
echo -e "${BLUE}Size:   ${NC}$(wc -l < "$OUTPUT_FILE") lines"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review:  cat $OUTPUT_FILE"
echo "  2. Edit:    vim $OUTPUT_FILE  (if needed)"
echo "  3. Send:    Open in your email or PDF converter"
echo ""
echo -e "${GREEN}Done!${NC}"
