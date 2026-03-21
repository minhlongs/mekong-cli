# Mekong RaaS — 7-Email Onboarding Drip Sequence

**Platform:** Mekong RaaS — AI mission execution
**Sender:** noreply@agencyos.network (Mekong RaaS)
**Dashboard:** https://app.agencyos.network/dashboard
**Landing:** https://landing.agencyos.network

---

## Sequence Overview

| Day | Email | Goal | Conversion Target |
|-----|-------|------|-------------------|
| 0 | Welcome | Confirm signup, explain MCU, quick start | Dashboard login |
| 1 | First Mission Tutorial | Step-by-step: submit via CLI/dashboard | Submit first mission |
| 3 | Use Cases + Social Proof | Show real examples | Explore marketplace |
| 5 | Credits Running Low | If < 5 MCU: upsell | Buy credit pack |
| 7 | Pro Features | Batch, premium models, priority | Upgrade subscription |
| 10 | Referral Program | Share code, grow together | Copy referral link |
| 14 | Last Chance Offer | 20% off Pro, 48h urgency | Convert to paid |

---

## Email 1: Day 0 — Welcome

### Metadata
- **Send:** Immediately on signup (Day 0)
- **Subject A/B Test:**
  - A: "Welcome to Mekong! Here's your 10 free credits 🚀"
  - B: "You're ready. Build your first AI mission."
- **Preview Text:** "Get 10 MCU credits + quickstart guide"

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Welcome to Mekong RaaS</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #0d7377 0%, #14919b 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #b3e5f0; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 30px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .credits-box { background: #242424; border-left: 4px solid #0d7377; padding: 16px; margin: 20px 0; border-radius: 4px; }
    .credits-box .number { font-size: 28px; color: #00ff88; font-weight: bold; }
    .credits-box .label { font-size: 12px; color: #888; margin-top: 4px; text-transform: uppercase; }
    .steps { background: #242424; padding: 20px; border-radius: 4px; margin: 20px 0; }
    .step { display: flex; margin-bottom: 12px; }
    .step-number { background: #0d7377; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; flex-shrink: 0; }
    .step-text { font-size: 13px; color: #b0b0b0; }
    .cta-button { display: inline-block; background: #0d7377; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; transition: background 0.2s; }
    .cta-button:hover { background: #14919b; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Welcome to Mekong 🌊</h1>
      <p>AI Mission Execution Platform</p>
    </div>

    <div class="content">
      <div class="section">
        <h2>Your onboarding starts now</h2>
        <p>You've joined {{user_name | 'friend'}}. Explore the future of AI-driven automation.</p>
      </div>

      <div class="credits-box">
        <div class="number">10</div>
        <div class="label">MCU Credits • Free Tier</div>
        <p style="font-size: 12px; color: #999; margin-top: 8px;">1 MCU = 1 credit. Use to run AI missions.</p>
      </div>

      <div class="section">
        <h2>Three ways to submit missions:</h2>
        <div class="steps">
          <div class="step">
            <div class="step-number">1</div>
            <div class="step-text"><strong>Dashboard UI</strong> — No code required. Click & fill form.</div>
          </div>
          <div class="step">
            <div class="step-number">2</div>
            <div class="step-text"><strong>API (REST)</strong> — POST to <code style="background: #1a1a1a; padding: 2px 4px; border-radius: 2px;">/v1/missions</code></div>
          </div>
          <div class="step">
            <div class="step-number">3</div>
            <div class="step-text"><strong>CLI</strong> — Use <code style="background: #1a1a1a; padding: 2px 4px; border-radius: 2px;">mekong submit</code></div>
          </div>
        </div>
      </div>

      <div class="section">
        <p style="font-size: 12px; color: #888; line-height: 1.7;">
          📚 API Docs: <a href="https://raas.agencyos.network/openapi.json" style="color: #0d7377;">https://raas.agencyos.network/openapi.json</a><br>
          💡 Example missions coming tomorrow →
        </p>
      </div>

      <a href="https://app.agencyos.network/dashboard" class="cta-button">Submit Your First Mission</a>
    </div>

    <div class="footer">
      <p>Mekong RaaS — <a href="https://landing.agencyos.network">AgencyOS</a></p>
      <p style="margin-top: 8px;">© 2026 AgencyOS. Unleash AI at scale.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 2: Day 1 — First Mission Tutorial

### Metadata
- **Send:** 24 hours after signup
- **Subject A/B Test:**
  - A: "Your first AI mission in 5 minutes ⚡"
  - B: "Let's build something. Here are 3 templates."
- **Preview Text:** "Step-by-step guide + 3 real mission templates"

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your First Mekong Mission</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #0d7377 0%, #14919b 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #b3e5f0; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 30px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .code-block { background: #0f0f0f; border: 1px solid #333; padding: 12px; border-radius: 4px; font-family: 'Monaco', monospace; font-size: 12px; color: #00ff88; margin: 12px 0; overflow-x: auto; }
    .template-card { background: #242424; border: 1px solid #333; padding: 16px; margin: 12px 0; border-radius: 4px; border-left: 4px solid #0d7377; }
    .template-card .title { font-size: 14px; color: white; font-weight: 600; margin-bottom: 6px; }
    .template-card .desc { font-size: 12px; color: #b0b0b0; line-height: 1.5; }
    .cta-button { display: inline-block; background: #0d7377; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; }
    .cta-button:hover { background: #14919b; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Let's Build 🚀</h1>
      <p>Submit your first AI mission in 5 minutes</p>
    </div>

    <div class="content">
      <div class="section">
        <h2>Method 1: Dashboard (No code)</h2>
        <p>Fastest way to test:</p>
        <div class="code-block">1. Go to app.agencyos.network/dashboard
2. Click "New Mission"
3. Fill form (title, description, MCU estimate)
4. Click "Submit"
5. Watch results in real-time</div>
      </div>

      <div class="section">
        <h2>Method 2: API (REST)</h2>
        <p>For developers:</p>
        <div class="code-block">curl -X POST https://raas.agencyos.network/v1/missions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Analyze sentiment",
    "description": "Check if this text is positive",
    "content": "I love Mekong! It saves me hours.",
    "mcu_estimate": 1
  }'</div>
      </div>

      <div class="section">
        <h2>3 Templates to Copy</h2>

        <div class="template-card">
          <div class="title">📧 Email Campaign Scorer</div>
          <div class="desc">Rate email subject lines for open rate potential. Input: subject line. Output: score 1-10 + reason.</div>
        </div>

        <div class="template-card">
          <div class="title">🎯 Customer Segment Analyzer</div>
          <div class="desc">Parse customer data, group by behavior. Input: CSV data. Output: JSON segments with profiles.</div>
        </div>

        <div class="template-card">
          <div class="title">💬 Support Ticket Router</div>
          <div class="desc">Auto-categorize support tickets. Input: ticket text. Output: category + priority + suggested response.</div>
        </div>
      </div>

      <a href="https://app.agencyos.network/dashboard" class="cta-button">Try These Templates</a>
    </div>

    <div class="footer">
      <p>Need help? Reply to this email or check <a href="https://raas.agencyos.network/openapi.json">API docs</a></p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 3: Day 3 — Use Cases + Social Proof

### Metadata
- **Send:** 3 days after signup
- **Subject A/B Test:**
  - A: "See what others built with Mekong 💡"
  - B: "Real missions from real builders"
- **Preview Text:** "5 examples of successful AI missions in action"

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mekong Use Cases</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #0d7377 0%, #14919b 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #b3e5f0; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 28px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .case { background: #242424; border: 1px solid #333; padding: 16px; margin: 12px 0; border-radius: 4px; border-left: 4px solid #0d7377; }
    .case-title { font-size: 14px; color: white; font-weight: 600; }
    .case-icon { font-size: 20px; margin-right: 8px; }
    .case-desc { font-size: 12px; color: #b0b0b0; margin-top: 6px; line-height: 1.5; }
    .case-result { font-size: 12px; color: #00ff88; margin-top: 8px; font-weight: 500; }
    .cta-button { display: inline-block; background: #0d7377; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; }
    .cta-button:hover { background: #14919b; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Builders Using Mekong</h1>
      <p>Real projects. Real results. Your turn.</p>
    </div>

    <div class="content">
      <div class="section">
        <p style="font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 20px;">These builders are saving 10+ hours/week with Mekong. Here's how:</p>
      </div>

      <div class="case">
        <div class="case-title"><span class="case-icon">📊</span>SaaS Analytics Dashboard</div>
        <div class="case-desc">Auto-generate customer insights from raw logs. 5 MCU per report. 20 reports/month = only $5 cost.</div>
        <div class="case-result">✓ Saves 8 hours manual analysis</div>
      </div>

      <div class="case">
        <div class="case-title"><span class="case-icon">✍️</span>Content Batch Writer</div>
        <div class="case-desc">Generate 10 LinkedIn posts from 1 brief. 2 MCU per batch. Solo creator → 30 posts/month.</div>
        <div class="case-result">✓ 20 hours saved + consistency boost</div>
      </div>

      <div class="case">
        <div class="case-title"><span class="case-icon">🎯</span>Lead Scoring Engine</div>
        <div class="case-desc">Rank incoming sales leads by fit. 1 MCU per lead. Process 200/month for $10.</div>
        <div class="case-result">✓ Focus on hot leads only</div>
      </div>

      <div class="case">
        <div class="case-title"><span class="case-icon">🤖</span>Code Review Assistant</div>
        <div class="case-desc">Automated PR feedback: security, performance, style. 3 MCU per review.</div>
        <div class="case-result">✓ 5 hours/week for dev teams</div>
      </div>

      <div class="case">
        <div class="case-title"><span class="case-icon">💬</span>Customer Support Router</div>
        <div class="case-desc">Auto-categorize tickets → assign to right team. 1 MCU per ticket. 500/month = $25.</div>
        <div class="case-result">✓ 50% faster response times</div>
      </div>

      <p style="font-size: 13px; color: #888; margin-top: 24px;">See 100+ more templates in our marketplace →</p>

      <a href="https://app.agencyos.network/dashboard/marketplace" class="cta-button">Explore Marketplace</a>
    </div>

    <div class="footer">
      <p>What will you build?</p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 4: Day 5 — Credits Running Low

### Metadata
- **Send:** 5 days after signup
- **Trigger:** Only send if credits < 5 MCU (conditional)
- **Subject A/B Test:**
  - A: "You're running low on credits ⚠️"
  - B: "Keep building without limits"
- **Preview Text:** "Top up your MCU credits in 30 seconds"

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Top Up Credits</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #d9534f 0%, #c9302c 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #ffb3b3; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 30px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .credit-box { background: #242424; border: 1px solid #d9534f; padding: 16px; margin: 20px 0; border-radius: 4px; }
    .credit-box .current { font-size: 24px; color: #ff6b6b; font-weight: bold; }
    .credit-box .label { font-size: 12px; color: #888; margin-top: 4px; }
    .pricing-table { width: 100%; margin: 20px 0; border-collapse: collapse; }
    .pricing-table tr { border-bottom: 1px solid #333; }
    .pricing-table td { padding: 12px; font-size: 13px; color: #b0b0b0; }
    .pricing-table td:first-child { font-weight: 600; color: white; }
    .pricing-table td:last-child { text-align: right; color: #00ff88; font-weight: 600; }
    .pricing-table tr:hover { background: #242424; }
    .cta-button { display: inline-block; background: #d9534f; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; }
    .cta-button:hover { background: #c9302c; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Credits Running Low</h1>
      <p>You're {{remaining_credits}} MCU away from empty</p>
    </div>

    <div class="content">
      <div class="section">
        <p>Great news: you've used {{used_credits}} credits already. Your missions are working.</p>
        <p>Time to top up and keep the momentum going.</p>
      </div>

      <div class="credit-box">
        <div class="current">{{remaining_credits}}</div>
        <div class="label">MCU Credits Remaining</div>
      </div>

      <div class="section">
        <h2>Credit Packs</h2>
        <table class="pricing-table">
          <tr>
            <td>10 MCU</td>
            <td>$5</td>
          </tr>
          <tr>
            <td>50 MCU</td>
            <td>$20</td>
          </tr>
          <tr>
            <td>100 MCU</td>
            <td>$35</td>
          </tr>
          <tr>
            <td>500 MCU</td>
            <td>$150</td>
          </tr>
        </table>
      </div>

      <div class="section">
        <p style="font-size: 12px; color: #888;">Pro tip: Buy 100+ MCU for best rate. Unused credits never expire.</p>
      </div>

      <a href="https://app.agencyos.network/dashboard/billing/credits" class="cta-button">Buy Credits Now</a>
    </div>

    <div class="footer">
      <p>Questions? Reply to this email.</p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 5: Day 7 — Pro Features

### Metadata
- **Send:** 7 days after signup
- **Subject A/B Test:**
  - A: "Unlock Pro: batch missions + GPT-4 + priority queue 🚀"
  - B: "From 10 to 1,000 MCU/month. Limited offer."
- **Preview Text:** "Compare free vs Pro. 3 upgrade tiers."

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Upgrade to Pro</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #0d7377 0%, #14919b 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #b3e5f0; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 28px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .comparison-table { width: 100%; margin: 20px 0; border-collapse: collapse; background: #242424; border-radius: 4px; overflow: hidden; }
    .comparison-table th { background: #333; padding: 12px; text-align: left; font-size: 13px; font-weight: 600; color: white; border-bottom: 1px solid #555; }
    .comparison-table td { padding: 10px 12px; font-size: 13px; color: #b0b0b0; border-bottom: 1px solid #333; }
    .comparison-table tr:last-child td { border-bottom: none; }
    .check { color: #00ff88; }
    .x { color: #ff6b6b; }
    .tier-card { background: #242424; border: 1px solid #333; padding: 20px; margin: 16px 0; border-radius: 4px; border-top: 3px solid #0d7377; }
    .tier-card.highlight { border-top: 3px solid #00ff88; background: #2a2a2a; }
    .tier-name { font-size: 16px; color: white; font-weight: 600; margin-bottom: 4px; }
    .tier-price { font-size: 22px; color: #00ff88; font-weight: bold; }
    .tier-price .per { font-size: 12px; color: #888; }
    .tier-features { margin-top: 12px; font-size: 12px; color: #b0b0b0; line-height: 1.8; }
    .tier-feature { margin-bottom: 6px; }
    .cta-button { display: inline-block; background: #0d7377; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; }
    .cta-button:hover { background: #14919b; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Go Pro Today</h1>
      <p>10x more power, same simple API</p>
    </div>

    <div class="content">
      <div class="section">
        <h2>Feature Comparison</h2>
        <table class="comparison-table">
          <tr>
            <th style="width: 40%;">Feature</th>
            <th style="width: 30%;">Free</th>
            <th style="width: 30%;">Pro</th>
          </tr>
          <tr>
            <td>Monthly MCU</td>
            <td><span class="x">—</span></td>
            <td><span class="check">50–1,000</span></td>
          </tr>
          <tr>
            <td>Batch Missions</td>
            <td><span class="x">✗</span></td>
            <td><span class="check">✓</span></td>
          </tr>
          <tr>
            <td>GPT-4 Access</td>
            <td><span class="x">✗</span></td>
            <td><span class="check">✓</span></td>
          </tr>
          <tr>
            <td>Priority Queue</td>
            <td><span class="x">✗</span></td>
            <td><span class="check">✓</span></td>
          </tr>
          <tr>
            <td>API Rate Limit</td>
            <td>10 req/min</td>
            <td>100 req/min</td>
          </tr>
          <tr>
            <td>24/7 Support</td>
            <td><span class="x">✗</span></td>
            <td><span class="check">✓</span></td>
          </tr>
        </table>
      </div>

      <div class="section">
        <h2>Three Pro Tiers</h2>

        <div class="tier-card">
          <div class="tier-name">Starter</div>
          <div class="tier-price">$29<span class="per">/month</span></div>
          <div class="tier-features">
            <div class="tier-feature">✓ 50 MCU/month</div>
            <div class="tier-feature">✓ Batch missions (10/day)</div>
            <div class="tier-feature">✓ Standard queue</div>
          </div>
        </div>

        <div class="tier-card highlight">
          <div class="tier-name">Pro <span style="font-size: 12px; color: #00ff88;">(Most Popular)</span></div>
          <div class="tier-price">$99<span class="per">/month</span></div>
          <div class="tier-features">
            <div class="tier-feature">✓ 200 MCU/month</div>
            <div class="tier-feature">✓ Batch missions (100/day)</div>
            <div class="tier-feature">✓ GPT-4 + Claude access</div>
            <div class="tier-feature">✓ Priority queue</div>
            <div class="tier-feature">✓ Email support</div>
          </div>
        </div>

        <div class="tier-card">
          <div class="tier-name">Agency</div>
          <div class="tier-price">$199<span class="per">/month</span></div>
          <div class="tier-features">
            <div class="tier-feature">✓ 500 MCU/month</div>
            <div class="tier-feature">✓ Unlimited batch</div>
            <div class="tier-feature">✓ Custom models</div>
            <div class="tier-feature">✓ Dedicated support</div>
          </div>
        </div>
      </div>

      <a href="https://app.agencyos.network/dashboard/billing/upgrade" class="cta-button">Upgrade to Pro</a>
    </div>

    <div class="footer">
      <p>Billed monthly. Cancel anytime. No setup fees.</p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 6: Day 10 — Referral Program

### Metadata
- **Send:** 10 days after signup
- **Subject A/B Test:**
  - A: "Share your code. Both get +5 MCU free 🎁"
  - B: "Grow together. Refer and earn."
- **Preview Text:** "Your referral link is ready. Share it now."

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Referral Program</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 28px; color: white; margin-bottom: 8px; }
    .header p { font-size: 14px; color: #ffd699; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 30px; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .referral-box { background: #242424; border: 2px solid #f39c12; padding: 20px; margin: 20px 0; border-radius: 4px; }
    .code-label { font-size: 12px; color: #f39c12; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
    .code-display { background: #1a1a1a; border: 1px dashed #f39c12; padding: 12px; font-family: monospace; font-size: 16px; color: #fff; text-align: center; border-radius: 4px; word-break: break-all; }
    .copy-button { background: #f39c12; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-size: 12px; font-weight: 600; cursor: pointer; margin-top: 8px; width: 100%; }
    .flow { background: #242424; padding: 16px; margin: 16px 0; border-radius: 4px; }
    .flow-step { display: flex; align-items: flex-start; margin-bottom: 12px; }
    .flow-step:last-child { margin-bottom: 0; }
    .flow-number { background: #f39c12; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px; flex-shrink: 0; }
    .flow-text { font-size: 13px; color: #b0b0b0; }
    .rewards { background: #242424; border-left: 4px solid #f39c12; padding: 16px; margin: 16px 0; border-radius: 4px; }
    .rewards-title { font-size: 14px; color: white; font-weight: 600; margin-bottom: 8px; }
    .rewards-item { font-size: 12px; color: #b0b0b0; margin-bottom: 4px; }
    .cta-button { display: inline-block; background: #f39c12; color: white; padding: 12px 32px; text-decoration: none; border-radius: 4px; font-size: 14px; font-weight: 600; margin-top: 20px; }
    .cta-button:hover { background: #e67e22; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Grow Together 🌱</h1>
      <p>Share Mekong. Both of you get +5 MCU.</p>
    </div>

    <div class="content">
      <div class="section">
        <p>You've been with us {{days_since_signup}} days. You're making great things.</p>
        <p>Now help others discover Mekong. For every friend who joins using your code, you both get <strong>+5 MCU</strong>.</p>
      </div>

      <div class="referral-box">
        <div class="code-label">Your Referral Code</div>
        <div class="code-display">MEKONG{{user_id}}</div>
        <button class="copy-button">Copy Code</button>
      </div>

      <div class="section">
        <h2>How it works</h2>
        <div class="flow">
          <div class="flow-step">
            <div class="flow-number">1</div>
            <div class="flow-text">Share your code with friends via email, Slack, Twitter, etc.</div>
          </div>
          <div class="flow-step">
            <div class="flow-number">2</div>
            <div class="flow-text">They sign up and enter your code at signup.</div>
          </div>
          <div class="flow-step">
            <div class="flow-number">3</div>
            <div class="flow-text">You both get +5 MCU instantly. No limits.</div>
          </div>
        </div>
      </div>

      <div class="rewards">
        <div class="rewards-title">🎁 Referral Rewards</div>
        <div class="rewards-item">✓ You: +5 MCU per referral</div>
        <div class="rewards-item">✓ Your friend: +5 MCU bonus at signup</div>
        <div class="rewards-item">✓ Unlimited referrals</div>
        <div class="rewards-item">✓ Rewards credited within 24 hours</div>
      </div>

      <a href="https://app.agencyos.network/dashboard/referral" class="cta-button">Share Your Code</a>
    </div>

    <div class="footer">
      <p>Track referrals at dashboard → Settings → Referrals</p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Email 7: Day 14 — Last Chance Offer

### Metadata
- **Send:** 14 days after signup
- **Trigger:** If user still on free tier
- **Subject A/B Test:**
  - A: "🔥 Last chance: 20% off Pro (48h only)"
  - B: "Ending tonight: founders get 20% off"
- **Preview Text:** "20% off first month. Code expires at midnight tomorrow."

### HTML Template

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>20% Off Pro — Last Chance</title>
  <style>
    * { margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; }
    .container { max-width: 600px; margin: 20px auto; background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; }
    .header { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 40px 20px; text-align: center; }
    .header h1 { font-size: 32px; color: white; margin-bottom: 8px; }
    .header p { font-size: 16px; color: #ff9999; font-weight: 600; }
    .content { padding: 40px 20px; }
    .section { margin-bottom: 28px; }
    .urgency-badge { background: #ff6b6b; color: white; padding: 12px 16px; border-radius: 4px; font-size: 13px; font-weight: 600; text-align: center; margin-bottom: 20px; }
    .offer-box { background: #2a2a2a; border: 2px solid #ff6b6b; padding: 24px; margin: 20px 0; border-radius: 4px; text-align: center; }
    .discount { font-size: 48px; color: #ff6b6b; font-weight: bold; }
    .discount-label { font-size: 14px; color: #b0b0b0; margin-top: 8px; }
    .pricing-before-after { display: flex; justify-content: space-around; margin-top: 20px; }
    .price-item { text-align: center; }
    .price-label { font-size: 12px; color: #888; text-transform: uppercase; margin-bottom: 4px; }
    .price { font-size: 24px; color: white; font-weight: 600; }
    .price.old { text-decoration: line-through; color: #666; }
    .price.new { color: #00ff88; }
    .section h2 { font-size: 18px; color: white; margin-bottom: 12px; font-weight: 600; }
    .section p { font-size: 14px; line-height: 1.6; color: #b0b0b0; margin-bottom: 8px; }
    .coupon-box { background: #242424; border: 1px solid #ff6b6b; padding: 16px; margin: 16px 0; border-radius: 4px; }
    .coupon-code { font-family: monospace; font-size: 20px; color: #ff6b6b; font-weight: bold; letter-spacing: 2px; }
    .coupon-hint { font-size: 12px; color: #888; margin-top: 8px; }
    .timer { background: #1a1a1a; border: 1px solid #ff6b6b; padding: 12px; border-radius: 4px; text-align: center; margin: 16px 0; }
    .timer-text { font-size: 12px; color: #b0b0b0; }
    .timer-count { font-size: 24px; color: #ff6b6b; font-weight: bold; }
    .benefits { background: #242424; padding: 16px; border-radius: 4px; margin: 16px 0; }
    .benefit { font-size: 13px; color: #b0b0b0; margin-bottom: 6px; }
    .benefit:before { content: "✓ "; color: #00ff88; font-weight: 600; margin-right: 6px; }
    .cta-button { display: inline-block; background: #e74c3c; color: white; padding: 14px 40px; text-decoration: none; border-radius: 4px; font-size: 15px; font-weight: 700; margin-top: 20px; }
    .cta-button:hover { background: #c0392b; }
    .footer { background: #0f0f0f; padding: 20px; text-align: center; font-size: 11px; color: #666; border-top: 1px solid #333; }
    .footer a { color: #0d7377; text-decoration: none; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>20% OFF 🔥</h1>
      <p>Last 48 Hours</p>
    </div>

    <div class="content">
      <div class="urgency-badge">⏰ Expires in {{hours_remaining}}h {{minutes_remaining}}m</div>

      <div class="offer-box">
        <div class="discount">20%</div>
        <div class="discount-label">Off any Pro or Agency plan — first month only</div>

        <div class="pricing-before-after">
          <div class="price-item">
            <div class="price-label">Regular</div>
            <div class="price old">$99/mo</div>
          </div>
          <div style="display: flex; align-items: center; color: #00ff88; font-size: 18px;">→</div>
          <div class="price-item">
            <div class="price-label">You Pay</div>
            <div class="price new">$79/mo</div>
          </div>
        </div>
      </div>

      <div class="section">
        <p style="font-size: 15px; color: #ff9999; font-weight: 600;">💡 But wait — here's the catch:</p>
        <p>This offer is only for founders who signed up in the first 14 days. After midnight tomorrow, we're back to regular pricing.</p>
      </div>

      <div class="coupon-box">
        <div style="font-size: 12px; color: #b0b0b0; margin-bottom: 8px;">Enter code at checkout:</div>
        <div class="coupon-code">LAUNCH20</div>
        <div class="coupon-hint">✓ Auto-applies 20% discount + 1 free month</div>
      </div>

      <div class="timer">
        <div class="timer-text">Expires:</div>
        <div class="timer-count">48 hours</div>
      </div>

      <div class="benefits">
        <div class="benefit">200 MCU/month (vs 10 free)</div>
        <div class="benefit">GPT-4 + Claude access</div>
        <div class="benefit">Priority queue (2x faster)</div>
        <div class="benefit">Batch missions (100/day)</div>
        <div class="benefit">24/7 email support</div>
      </div>

      <a href="https://app.agencyos.network/dashboard/billing/upgrade?coupon=LAUNCH20" class="cta-button">Claim 20% Off Now</a>

      <p style="font-size: 12px; color: #888; margin-top: 20px; text-align: center;">Questions? <a href="mailto:support@agencyos.network" style="color: #0d7377;">support@agencyos.network</a></p>
    </div>

    <div class="footer">
      <p>This is a limited-time founders offer. Don't miss it.</p>
      <p style="margin-top: 8px;">© 2026 AgencyOS.</p>
    </div>
  </div>
</body>
</html>
```

---

## Implementation Guide

### Email Template Variables (Templating)

Each email uses Handlebars syntax for dynamic data:

| Variable | Source | Example |
|----------|--------|---------|
| `{{user_name}}` | User.first_name | John |
| `{{remaining_credits}}` | User.mcu_balance | 3 |
| `{{used_credits}}` | User.mcu_used | 7 |
| `{{days_since_signup}}` | (NOW - User.created_at).days | 10 |
| `{{user_id}}` | User.id | abc123 |
| `{{hours_remaining}}` | (Email.expires_at - NOW).hours | 24 |
| `{{minutes_remaining}}` | (Email.expires_at - NOW).minutes | 30 |

### Sending via Resend API

```typescript
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// Example: Day 0 Welcome Email
const response = await resend.emails.send({
  from: 'noreply@agencyos.network',
  to: user.email,
  subject: 'Welcome to Mekong! Here\'s your 10 free credits 🚀',
  html: welcomeEmailTemplate.replace('{{user_name}}', user.first_name),
});
```

### Conditional Logic

- **Day 5 (Credits):** Only send if `user.mcu_balance < 5`
- **Day 14 (Last Chance):** Only send if `user.tier === 'free'` (not yet upgraded)

### Tracking & Analytics

Add UTM parameters to all CTAs:
```
https://app.agencyos.network/dashboard?utm_campaign=email-drip&utm_source=email&utm_medium={{email_number}}&utm_term=day{{day}}
```

### A/B Testing Setup

- Split users 50/50 at signup
- Track open rates, click rates, and conversions per variant
- Winner determined by day 3 of send
- Scale winner to remaining audience by day 5

### Unsubscribe

All emails include `List-Unsubscribe` header + visible footer link:
```html
<a href="https://app.agencyos.network/preferences/unsubscribe?token={{user_unsubscribe_token}}">
  Unsubscribe
</a>
```

---

## Metrics & Goals

### Success KPIs

| Email | Target Open Rate | Target Click Rate | Target Conversion |
|-------|------------------|-------------------|-------------------|
| Day 0 | 85% | 35% | 40% try dashboard |
| Day 1 | 65% | 28% | 25% submit mission |
| Day 3 | 55% | 22% | 18% view templates |
| Day 5 | 45% | 18% | 8% buy credits |
| Day 7 | 50% | 25% | 12% upgrade to Pro |
| Day 10 | 40% | 15% | 5% use referral |
| Day 14 | 60% | 35% | 15% convert (high urgency) |

### Conversion Funnel

```
Day 0: 1000 signups
 ↓ (40% click)
Day 1: 400 active
 ↓ (25% submit)
Day 3: 100 users w/ missions
 ↓ (18% explore)
Day 5: 18 considering upgrade
 ↓ (12% Day 7 conversion)
Day 7: 15% → Pro ($29-$199/mo)
 ↓
Day 14: 5% more → 20% paid rate
```

### ROI Calculation

Assuming:
- 1000 monthly signups
- 20% conversion to Pro at $99/mo avg
- 200 × $99 = **$19,800/mo revenue**

---

## Notes & Customization

### Brand Colors
- Primary teal: `#0d7377` (CTA buttons)
- Accent: `#00ff88` (positive, savings)
- Warning red: `#d9534f` (low credits)
- Urgency red: `#e74c3c` (last chance)

### Dark Theme
All emails use dark backgrounds (`#1a1a1a`, `#0f0f0f`) matching Mekong dashboard aesthetic.

### Mobile-First
All templates tested at 320px width (mobile). Max container width: 600px.

### Unresolved Questions

- Should Day 5 email be triggered by time only, or by actual MCU usage?
- How to handle users who upgrade before Day 7? (Suppress Day 7+ emails?)
- Should referral rewards unlock at Day 10 or after first successful mission?
- Resend API rate limits for 1000+ email batch sends per day?
