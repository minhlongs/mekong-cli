# Polar.sh Organization Rejection Analysis: mekong-cli

**Research Date:** 2026-03-26
**Status:** Complete
**Token Efficiency:** High

---

## Executive Summary

Polar.sh rejects organization creation primarily based on **product category compliance** and **KYC/account review findings**. The "mekong-cli" rejection likely stems from one of three vectors:

1. **Product category flagging** (automated or manual)
2. **Business model mismatch** (Polar requires digital goods; tool distribution may not fit)
3. **Account review red flags** (failed KYC, suspicious patterns, or re-flagging after prior incident)

---

## Key Findings

### 1. Polar.sh PROHIBITED Categories (Hard Blocks)

Polar explicitly bans these product types — organizations selling these get **automatic rejection**:

**Critical for mekong-cli:**
- ❌ **Trading/Financial Services** (including bots, investment advisory, trading signals)
- ❌ **Unregulated financial services**
- ❌ **AI relationship/content services** (if positioned as such)
- ❌ **OSINT platforms** (unauthorized data access)
- ❌ **Cheating/hack tools**

**General Prohibitions:**
- ❌ Adult content, gambling, illegal goods
- ❌ Unauthorized content downloading
- ❌ IP infringement enabling
- ❌ Services facilitating unauthorized data access

**Orange Flags (Require Pre-Review):**
- 🟡 Marketing/outreach services
- 🟡 VPN services
- 🟡 Pre-orders/waitlists
- 🟡 eBooks and restricted business types

### 2. Why Polar Rejects Organizations

**Risk Mitigation Drivers:**
- High chargeback/refund risk
- Legal liability concerns
- Reputational damage
- Card network (Visa/Mastercard) violations
- Non-compliance with MoR regulations

### 3. Account Review Process

**Timeline:**
- Average: **~1 week** for approval
- Longer if: Weekends, holidays, or complexity flags
- **Rejection:** No published timeline; appears immediate or after review

**KYC Requirements:**
- Identity verification (Passport/ID/Driver License)
- Selfie verification
- Business survey (intended use case, products, revenue model)
- Email confirmation

**Previous Context:** The "Wellneusraas" account was flagged 2026-03-23 for medical/wellness keyword usage — **Polar interpreted this as regulated healthcare services**, triggering account suspension despite being a legitimate SaaS business.

### 4. CLI Tool & Automation Products on Polar

**Allowed:** Command-line tools for developer productivity, software distribution
**Not Allowed:** CLI tools that facilitate unauthorized access, cheating, or financial manipulation

**Current Polar Position:**
- Polar itself uses/endorses CLI tools (e.g., `polar listen` for webhook testing)
- CLI distribution is acceptable IF the underlying product is compliant
- Problem: If "mekong-cli" is positioned as **automation/agent/bot platform**, Polar may flag it as:
  - ❌ Potential financial bot (if capable of trading/investment decisions)
  - ❌ Unauthorized automation tool (if it accesses third-party services without permission)
  - ❌ Cheating/exploit tool (if used to bypass systems)

---

## Likely Rejection Root Causes (Priority Order)

### 🔴 HIGH PRIORITY

1. **Product Description Contains Prohibited Keywords**
   - Same issue as "Wellneusraas" flagged 2026-03-23
   - If mekong-cli is marketed as: "AI automation," "trading bot," "financial agent," etc.
   - **Fix:** Audit product description; remove bot/automation/trading language; use neutral SaaS phrasing

2. **Business Model Mismatch**
   - If positioned as **fulfillment-requiring service** (consulting, development, agency work)
   - Polar only accepts digital goods: downloads, licenses, subscriptions, code repos
   - **Fix:** Clarify that mekong-cli is a **standalone software product**, not a service

3. **Account Tied to Prior Polar Incident**
   - Email/organization linked to the "Wellneusraas" suspension
   - Polar may auto-block related accounts as precaution
   - **Fix:** Use different email, business address, or contact Polar support directly

### 🟡 MEDIUM PRIORITY

4. **KYC or Identity Verification Failed**
   - Document submission rejected, illegible, or mismatched
   - **Fix:** Resubmit with clear, valid government ID

5. **Suspicious Activity Pattern**
   - Multiple org creation attempts in short period
   - Previous chargebacks, disputes, or refund spikes on Wellneusraas
   - **Fix:** Wait 48h, then contact Polar support; explain legitimate business case

---

## Action Items

### Immediate (Do First)

1. **Fetch Rejection Reason**
   - Check Polar email for specific rejection message
   - If no email: Log into Polar dashboard → Account settings → Review history
   - **Extract:** Rejection code/category (e.g., "Prohibited Category," "Failed KYC," "Account Review")

2. **Audit Product Description & Marketing Copy**
   - Search all uses of: "bot," "trading," "financial," "automation," "agent," "investment"
   - Remove/replace with: "CLI tool," "platform," "software," "infrastructure"
   - Example:
     - ❌ "mekong-cli: AI trading bot for financial markets"
     - ✅ "mekong-cli: Infrastructure automation CLI platform"

3. **Contact Polar Support (Email)**
   - Subject: "Organization Creation Rejected: mekong-cli — Request Review"
   - Include: Business description (3-4 sentences), specific product use case, clarification on any flagged keywords
   - Link to: Compliant product docs/repo
   - **Template:**
     ```
     mekong-cli is a developer infrastructure CLI tool for task automation
     and distributed system orchestration. It is positioned as B2B SaaS
     software, not a financial or consulting service. We believe the
     rejection may stem from keyword misinterpretation. Please advise
     on specific rejection reason.
     ```

### If First Attempt Fails

4. **Create New Organization with Different Email/Details**
   - Use different business email (e.g., company domain vs. personal)
   - New organization name (avoid "mekong," which may be cached in Polar's review system)
   - Fresh KYC docs

5. **Escalate to Polar Team (If Recurring)**
   - Check Polar GitHub issues: https://github.com/polarsource/polar
   - Post question in Polar community channels (Discord/community forum)
   - Tweet at @polar_sh; Polar actively responds to public inquiries

---

## Technical Notes

**No Evidence of Polar.sh Service Issues (March 2026)**
- Polar status page shows stable uptime across March 2026
- No published outages affecting organization creation
- Rejection is **policy-driven**, not infrastructure-driven

**Polar MCP Integration Available**
- Polar offers Model Context Protocol (MCP) server
- May be relevant for mekong-cli integration with Claude/LLM ecosystems
- Ensure product description aligns with Polar's integration-friendly positioning

---

## References

- [Polar.sh Acceptable Use Policy](https://polar.sh/docs/merchant-of-record/acceptable-use)
- [Polar.sh Account Reviews Process](https://polar.sh/docs/merchant-of-record/account-reviews)
- [Polar.sh Terms of Service](https://polar.sh/legal/terms)
- [Polar.sh Status](https://status.polar.com)
- [Polar GitHub](https://github.com/polarsource/polar)

---

## Unresolved Questions

1. **What is the exact rejection reason?** (Check Polar email/dashboard)
2. **Is mekong-cli positioned as a bot/automation service, or pure CLI tool?** (Affects recommendation)
3. **Is the account email linked to the prior "Wellneusraas" incident?** (If yes, new account needed)
4. **Does Polar have rate limits on organization creation re-attempts?** (Not documented publicly; test after 48h)
