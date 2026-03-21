# RaaS Support SOP (Standard Operating Procedure)

**Support escalation tiers, incident response, and customer issue resolution workflows.**

---

## Support Tier Structure

### Tier 1: Self-Service (No Cost)

**Hours:** 24/7 | **Response:** Immediate (self-service)

**Resources:**
- [Getting Started Guide](./raas-customer-onboarding.md) — Basic setup
- [API Documentation](./raas-api.md) — Technical reference
- [FAQ Section](#faq-common-issues) — Troubleshooting
- [Community Discord](https://mekong-cli.io/discord) — Peer support

**Who Uses:**
- New customers onboarding
- DIY troubleshooting
- Documentation reference

---

### Tier 2: Email Support (Standard)

**Hours:** Monday-Friday, 9am-6pm UTC | **SLA:** 24-hour response | **Cost:** Free (included)

**Channel:** support@agencyos.network

**Typical Issues:**
- API integration questions
- Mission failures with logs
- Billing inquiries
- Account access issues

**Escalation Trigger:** Issue unresolved after 48 hours

---

### Tier 3: Priority Support (Enterprise Only)

**Hours:** 24/7 | **SLA:** 4-hour response | **Cost:** Included in Enterprise tier ($499/month)

**Channels:**
- Dedicated Slack channel (real-time)
- Priority email queue
- Direct phone (emergency only)

**Typical Issues:**
- Production mission failures
- API rate limit concerns
- Custom architecture review
- Dedicated account manager

**Escalation Trigger:** Issue unresolved after 4 hours

---

## Common Issues & Resolution Matrix

### Issue 1: 401 Unauthorized (Invalid API Key)

| Symptom | Root Cause | Resolution |
|---------|-----------|-----------|
| Mission submission fails with 401 | Invalid/expired API key | 1. Verify key starts with `mk_`<br>2. Generate new key in dashboard<br>3. Update env var: `export MEKONG_API_KEY="mk_..."`<br>4. Retry mission |

**Self-Service Check:**
```bash
echo $MEKONG_API_KEY
# Should output: mk_xxxxx... (not empty or invalid)

mekong cloud whoami
# Should show your user/org (validates key is correct)
```

---

### Issue 2: 402 Payment Required (Insufficient Credits)

| Symptom | Root Cause | Resolution |
|---------|-----------|-----------|
| Mission queued indefinitely or rejected | Zero credit balance | 1. Check balance: `mekong cloud whoami`<br>2. Purchase tier: `mekong cloud billing checkout --tier pro`<br>3. Complete Polar.sh checkout<br>4. Retry mission (credits instant) |

**Prevention:**
- Set up billing alerts (Enterprise: automatic)
- Monitor usage monthly via `mekong cloud billing history`

---

### Issue 3: 403 Forbidden (Account Suspended)

| Symptom | Root Cause | Resolution |
|---------|-----------|-----------|
| All API calls rejected with 403 | Account deactivated (unpaid invoice, ToS violation) | 1. Check email for suspension notice<br>2. For payment: complete outstanding invoice via dashboard<br>3. For ToS: contact support@agencyos.network<br>4. Account reactivated within 24 hours |

**Escalate Immediately:** Email support@agencyos.network with screenshot of error.

---

### Issue 4: Mission Stuck in "Queued" Status

| Symptom | Root Cause | Resolution |
|---------|-----------|-----------|
| Mission status: "queued" for >10 minutes | High platform load or agent pickup delay | 1. Wait 2-3 minutes (normal queue depth varies)<br>2. Check dashboard status: [agencyos.network/dashboard/missions](https://agencyos.network/dashboard/missions)<br>3. If stuck >5 minutes:<br>&nbsp;&nbsp;a. Try: `mekong cloud mission cancel <id>`<br>&nbsp;&nbsp;b. Resubmit: `mekong cloud mission submit "..."`<br>4. If still stuck: email support with mission ID |

**Monitoring:**
```bash
# Poll with timeout
for i in {1..10}; do
  echo "Attempt $i..."
  STATUS=$(mekong cloud mission status $MISSION_ID)
  if [[ "$STATUS" != *"queued"* ]]; then break; fi
  sleep 30
done
```

---

### Issue 5: Mission Failed with Unclear Error

| Symptom | Root Cause | Resolution |
|---------|-----------|-----------|
| Status: "failed" + error message is cryptic | Mission timeout, resource limit, or codebase issue | 1. Get detailed logs: `mekong cloud mission logs <id>`<br>2. Check if it's timeout: Simplify mission (break into smaller parts)<br>3. Check logs for:"ERROR", "timeout", "OOM"<br>4. If unsolved: email support with mission ID + logs |

**Get Full Logs:**
```bash
mekong cloud mission logs <mission-id> > mission-logs.txt
cat mission-logs.txt | grep -i "error\|fail\|exception"
```

**Common Error Codes:**
- `TIMEOUT_30m` → Mission took >30 minutes (break into smaller tasks)
- `OOM_EXCEEDED` → Out of memory (codebase too large, try fewer files)
- `COMPILATION_ERROR` → Syntax error in target code (fix manually, retry)
- `AUTH_FAILED` → Git credentials missing (check repo access)

---

## Escalation Flowchart

```
Customer Issue
    ↓
[Step 1] Is this a billing issue?
    ├─ YES → Tier 2 Email (support@agencyos.network)
    │         SLA: 24h response
    └─ NO → [Step 2]

[Step 2] Did customer try self-service troubleshooting?
    ├─ NO → Direct to FAQ + Getting Started guide
    └─ YES → [Step 3]

[Step 3] Is customer Enterprise?
    ├─ YES → Tier 3 Priority (Slack + 4h SLA)
    │        Assign dedicated support engineer
    └─ NO → [Step 4]

[Step 4] Can issue be resolved via FAQ or docs?
    ├─ YES → Provide solution (Tier 1 Self-Service)
    └─ NO → Tier 2 Email Support
            SLA: 24h response
            If unresolved after 48h → escalate to engineering
```

---

## Incident Response Protocol

### Definition: Incident

An incident is any of:
- Platform-wide outage (API returning 5xx errors)
- Data loss or corruption affecting a tenant
- Security breach or vulnerability disclosure
- Customer unable to use RaaS for >30 minutes

### Incident Severity Levels

| Severity | Impact | Response Time | On-Call? |
|----------|--------|---------------|----------|
| **Critical** | Platform down, all customers affected | 15 minutes | Yes (24/7) |
| **High** | Feature unavailable, >10% customers impacted | 1 hour | Yes (business hours) |
| **Medium** | Degraded performance, <10% impacted | 4 hours | No (Tier 2 queue) |
| **Low** | Minor issue, cosmetic, 1 customer | 24 hours | No (regular queue) |

### Critical Incident Checklist

1. **Detection:** Customer reports via email/Slack or monitoring alert triggers
2. **Triage:** Confirm incident scope (how many customers? what feature?)
3. **Notification:** Post to #status Slack channel, update status page
4. **Investigation:** Identify root cause (logs, metrics, recent deployments)
5. **Mitigation:** Deploy fix or rollback problematic change
6. **Communication:** Update customers every 30 minutes with progress
7. **Resolution:** Incident resolved, all systems green
8. **Postmortem:** Team debrief within 24 hours, document findings

**Contact for Critical Incidents (Enterprise only):**
- Primary: support@agencyos.network
- Escalation: ops-team-pager@agencyos.network (auto-pages on-call engineer)

---

## Common Issues Escalation Decision Tree

```
Customer Report
  │
  ├─ "Mission won't submit"
  │  └─ Check: API key valid? Credits available? Rate limit hit?
  │     → Most resolved at Tier 1 (FAQ)
  │
  ├─ "Mission failed with error"
  │  └─ Provide logs, suggest break mission into smaller parts
  │     → Tier 2 if pattern repeats (engineering investigation)
  │
  ├─ "Platform is slow/down"
  │  └─ Check: status page or customer in different region?
  │     → Tier 3 (real incident) vs Tier 1 (expected congestion)
  │
  ├─ "Billing issue / incorrect charge"
  │  └─ Review mission logs, verify credits deducted correctly
  │     → Tier 2 + Finance team, typically resolved in 48h
  │
  └─ "I need custom feature"
     └─ Document request, schedule architectural review
        → Tier 3 (Enterprise) or Sales team (standard customers)
```

---

## Customer Feedback Loop

### Issue Reporting to Product Backlog

When a customer issue reveals a product gap:

1. **Categorize:** Is this a bug, missing feature, or UX improvement?
2. **Document:** Create GitHub issue with customer details (anonymized)
3. **Prioritize:**
   - Critical bugs (mission failures) → Sprint immediately
   - Feature requests → Backlog (prioritize by customer count)
   - UX improvements → Backlog (evaluate ROI)
4. **Update Customer:** Notify customer of planned fix/feature with ETA

**Example:** If 3 customers report "Can't see mission logs in real-time", escalate to product as missing feature.

---

## FAQ: Common Issues

### Q1: How long does support take to respond?

**A:**
- **Tier 1 (Self-Service):** Instant (docs are always available)
- **Tier 2 (Email):** <24 hours (usually <4h during business hours)
- **Tier 3 (Enterprise):** <4 hours (24/7)

### Q2: What if my issue isn't in the FAQ?

**A:** Email support@agencyos.network with:
- Your mission ID
- Full error message
- What you were trying to do
- Your RaaS tier

Response: <24 hours.

### Q3: Can I get a refund if a mission failed?

**A:** Yes. Zero charge for failed missions. If you were charged in error, contact support with mission ID and we'll refund within 24 hours.

### Q4: What if I disagree with the support decision?

**A:** Escalate to ops-team@agencyos.network for a second opinion. Enterprise customers can request a manager review.

### Q5: How do I report a security issue?

**A:** Do NOT post in public channels. Email security@agencyos.network with details. We acknowledge within 24 hours and work on fix confidentially.

### Q6: Can I speak to an engineer directly?

**A:**
- **Tier 2:** No (support team triages first)
- **Tier 3 (Enterprise):** Yes (dedicated account manager can arrange)

### Q7: What's the expected turnaround for bug fixes?

**A:**
- **Critical bugs:** Fixed in <24 hours (hotpatch deployed immediately)
- **High priority:** Fixed in 1-2 weeks (bundled in sprint)
- **Standard:** Backlogged (may take 1-3 months)

### Q8: Can I get custom SLA terms?

**A:** Enterprise customers only. Contact sales@agencyos.network to discuss uptime guarantees, response time SLAs, and dedicated infrastructure.

### Q9: How do I know if RaaS is having an outage?

**A:** Check [status.agencyos.network](https://status.agencyos.network) for real-time platform status.

### Q10: Is there a service status page?

**A:** Yes, [status.agencyos.network](https://status.agencyos.network). Subscribes to email/SMS alerts for incidents.

---

## Support Contact Information

### Email
- **General Support:** support@agencyos.network
- **Sales:** sales@agencyos.network
- **Security:** security@agencyos.network
- **Billing:** billing@agencyos.network

### Community
- **Discord:** [mekong-cli.io/discord](https://mekong-cli.io/discord)
- **GitHub Issues:** [github.com/mekong-ai/mekong-cli/issues](https://github.com/mekong-ai/mekong-cli/issues)

### Enterprise (Direct)
- **Slack:** Your dedicated #support channel (Enterprise customers only)
- **Account Manager:** Listed in your welcome email

---

## Support Hours by Tier

| Tier | Monday-Friday | Weekends | Holidays |
|------|---------------|----------|----------|
| Tier 1 (Self-Service) | 24/7 | 24/7 | 24/7 |
| Tier 2 (Email) | 9am-6pm UTC | No support | No support |
| Tier 3 (Enterprise) | 24/7 | 24/7 | 24/7 |

**Note:** Enterprise customers on critical incidents get 24/7 support regardless of day/time.

---

## SLA Guarantees

### Tier 2 SLA (Standard)

| Priority | Response Time | Resolution Time |
|----------|---------------|-----------------|
| Critical | 4 hours | 24 hours |
| High | 24 hours | 5 business days |
| Medium | 48 hours | 10 business days |
| Low | 5 business days | 30 days |

### Tier 3 SLA (Enterprise)

| Priority | Response Time | Resolution Time |
|----------|---------------|-----------------|
| Critical | 15 minutes | 4 hours |
| High | 1 hour | 8 hours |
| Medium | 4 hours | 1 business day |
| Low | 24 hours | 5 business days |

**SLA Credits:** If we miss SLA, Enterprise customers receive 10% month credit toward next invoice.

---

## Quality Standards

### Support Response Quality

We measure support by:
- **Response completeness:** Does answer fully address the issue?
- **Accuracy:** Is the answer correct and verified?
- **Professionalism:** Tone is helpful and respectful
- **Speed:** Response within SLA

### Customer Satisfaction

- Post-support survey sent after each support ticket
- Target NPS: >4.8/5.0 (Detractors followed up within 24h)
- Quarterly reviews with Enterprise customers

---

**Version:** 1.0.0 | **Last Updated:** 2026-03-21 | **Audience:** Support Team, Sales, Enterprise Customers

© 2026 Binh Phap Venture Studio. *"The supreme art of war is to subdue the enemy without fighting."*
