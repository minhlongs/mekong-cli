# Marketing Metrics & KPIs

**Purpose:** Track performance against content marketing strategy goals

**Reporting Cadence:**
- Daily: Engagement metrics (social)
- Weekly: Traffic, conversions, content performance
- Monthly: Full funnel review, strategy adjustment
- Quarterly: Strategic review, budget allocation

---

## Dashboard Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MARKETING DASHBOARD                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  TOFU    │  Visitors: _____ │  New subs: _____           │
│  Awareness│  (Goal: 5K/mo) │  (Goal: 1K/mo)            │
│          │  Trend: ↑↓→    │  Trend: ↑↓→               │
├──────────┼────────────────┼────────────────────────────┤
│  MOFU    │  Downloads: __ │  Demo reqs: __            │
│  Consider│  (Goal: 200/mo)│  (Goal: 50/mo)            │
│          │  Conv rate: __%│  → Trial: __%             │
├──────────┼────────────────┼────────────────────────────┤
│  BOFU    │  Trials: _____ │  Paid: _____              │
│  Convert │  (Goal: 100/mo)│  (Goal: 25/mo)            │
│          │  Conv rate: __%│  MRR: $______             │
├──────────┴────────────────┴────────────────────────────┤
│  SEO:    Keywords: ___ │  Org traffic: ___/mo         │
│  Social:  Followers: __│  Engagement: __%            │
│  Revenue: CAC: $____  │  LTV:CAC: __:1              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Top-of-Funnel Metrics (Awareness)

### Website Traffic
| Metric | Definition | Month 1 | Month 3 | Month 6 | Data Source |
|--------|------------|---------|---------|---------|-------------|
| Total visits | All sessions | 500 | 5,000 | 15,000 | GA4 |
| Unique visitors | Distinct users | 400 | 4,000 | 12,000 | GA4 |
| New vs. returning | % new visitors | 70% | 65% | 60% | GA4 |
| Traffic sources | Direct, organic, social, paid | Track mix | Track mix | Track mix | GA4 |
| Bounce rate | % leaving after 1 page | < 60% | < 55% | < 50% | GA4 |
| Pages/session | Depth of browsing | > 2 | > 2.5 | > 3 | GA4 |

### SEO Performance
| Metric | Definition | Target M3 | Target M6 | Data Source |
|--------|------------|-----------|-----------|-------------|
| Ranking keywords (top 10) | Keywords ranking 1-10 | 10 | 50 | Ahrefs |
| Organic traffic/month | GA organic sessions | 200 | 1,500 | GA4 |
| Avg. position | Position for tracked keywords | 25 | 15 | Ahrefs |
| Click-through rate | SERP CTR | 3% | 5% | Ahrefs |
| Domain rating | Ahrefs DR score | 10 | 25 | Ahrefs |
| Backlinks | Referring domains | 20 | 100 | Ahrefs |

### Social Media Reach
| Platform | Metric | Target M3 | Target M6 | Data Source |
|----------|--------|-----------|-----------|-------------|
| Twitter/X | Followers | 1,000 | 5,000 | Twitter Analytics |
| | Impressions/month | 50K | 250K | Twitter Analytics |
| | Engagement rate | 2% | 3% | Twitter Analytics |
| LinkedIn | Followers | 300 | 1,500 | LinkedIn Analytics |
| | Post views | 2,000/post | 10K/post | LinkedIn Analytics |
| YouTube | Subscribers | 200 | 1,000 | YouTube Analytics |
| | Views/month | 2K | 10K | YouTube Analytics |
| | Avg. watch time | 40% | 50% | YouTube Analytics |

---

## 2. Mid-Funnel Metrics (Consideration)

### Lead Generation
| Metric | Definition | Target M3 | Target M6 | Data Source |
|--------|------------|-----------|-----------|-------------|
| Newsletter subscribers | Email list size | 400 | 2,000 | ConvertKit |
| Email capture rate | % visitors → email | 2% | 4% | GA4 + ConvertKit |
| Lead magnet downloads | PDF/course downloads | 100 | 500 | ConvertKit |
| Demo requests | Form submissions | 30 | 100 | CRM |
| Free trial signups | Polar checkout starts | 50 | 250 | Polar API |

### Content Engagement
| Metric | Definition | Target M3 | Target M6 | Data Source |
|--------|------------|-----------|-----------|-------------|
| Blog avg. time on page | Engagement depth | > 2 min | > 3 min | GA4 |
| Blog returning visitors | % reading multiple posts | 20% | 30% | GA4 |
| Newsletter open rate | Opens / delivered | 18% | 22% | ConvertKit |
| Newsletter click rate | Clicks / opens | 2% | 4% | ConvertKit |
| Newsletter unsubscribe | Unsubs / total | < 0.5% | < 0.3% | ConvertKit |
| Video completion rate | Watched 75%+ | 30% | 40% | YouTube Analytics |

---

## 3. Bottom-of-Funnel Metrics (Conversion)

### Trial to Paid Conversion
| Metric | Definition | Target M3 | Target M6 | Data Source |
|--------|------------|-----------|-----------|-------------|
| Free trials started | Unique trial users | 50 | 250 | Polar API |
| Paid conversions | Trials → paid | 2-3 | 10-15 | Polar API |
| Conversion rate | % trials → paid | 4% | 6% | Calculated |
| Starter tier customers | $49/mo plan | 15 | 60 | Stripe/Polar |
| Growth tier customers | $149/mo plan | 5 | 20 | Stripe/Polar |
| Pro tier customers | $499/mo plan | 2 | 10 | Stripe/Polar |

### Revenue Metrics
| Metric | Definition | Target M3 | Target M6 | Data Source |
|--------|------------|-----------|-----------|-------------|
| MRR | Monthly recurring revenue | $1,500 | $10,000 | Stripe/Polar |
| ARR | Annual recurring revenue | $18K | $120K | Stripe/Polar |
| ARPU | Average revenue per user | $60 | $80 | Stripe/Polar |
| New MRR | MRR from new customers | $1K | $5K | Stripe/Polar |
| Expansion MRR | Upsells/add-ons | $0 | $500 | Stripe/Polar |
| Churn MRR | Lost MRR | $0 | $200 | Stripe/Polar |
| Net MRR | New - Churn | $1K | $4.3K | Calculated |

---

## 4. Cost & Efficiency Metrics

### CAC (Customer Acquisition Cost)
```
CAC = Total marketing spend / New customers acquired

Example: $3,000 spend / 10 customers = $300 CAC
```

| Metric | Target M3 | Target M6 | Calculation |
|--------|-----------|-----------|-------------|
| Total marketing spend | $1,500 | $5,000 | Financial records |
| New customers | 10 | 50 | Stripe/Polar |
| **CAC** | **$150** | **$100** | Spend / Customers |

### LTV (Customer Lifetime Value)
```
LTV = (ARPU × Gross margin %) / Churn rate

Example: ($80 × 90%) / 3% = $2,400
```

| Metric | Target M3 | Target M6 | Calculation |
|--------|-----------|-----------|-------------|
| ARPU | $60 | $80 | Stripe |
| Gross margin % | 90% | 90% | Finance |
| Monthly churn | 5% | 3% | Stripe |
| **LTV** | **$1,080** | **$2,400** | Formula above |

### LTV:CAC Ratio
| Metric | Target | Status |
|--------|--------|--------|
| LTV:CAC | > 3:1 | Calculating |

### CAC Payback Period
```
Payback (months) = CAC / (ARPU × Gross margin %)

Example: $150 / ($80 × 90%) = 2.1 months
```

| Metric | Target | Calculation |
|--------|--------|-------------|
| CAC Payback | < 6 months | CAC / (ARPU × 90%) |

---

## 5. Content Performance Metrics

### Blog Posts
| Metric | How to Track | Target |
|--------|--------------|--------|
| Pageviews | GA4 | 500/post (avg) |
| Avg. time on page | GA4 | > 3 min |
| Scroll depth | GA4 events | 75%+ scroll on 50%+ posts |
| Social shares | ShareThis/monitoring | 10+ shares/post |
| Backlinks | Ahrefs | 1-3 per post |
| Conversions | Lead magnet downloads from post | 2-5% |

### Newsletter
| Metric | How to Track | Target |
|--------|--------------|--------|
| Subscriber growth rate | ConvertKit | 20%/month |
| Open rate | ConvertKit | > 20% |
| Click rate | ConvertKit | > 3% |
| Unsubscribe rate | ConvertKit | < 0.5% |
| Replies | ConvertKit | 2%+ (engagement) |

### Social Media
| Metric | How to Track | Target |
|--------|--------------|--------|
| Follower growth | Platform analytics | 15%/month |
| Engagement rate | (Likes+RTs)/followers | 2-4% |
| Link clicks | UTM tracking | 5% of impressions |
| Profile visits | Platform analytics | 100/week |
| Conversion from social | UTM + checkout | 0.5% of clicks |

### Videos
| Metric | How to Track | Target |
|--------|--------------|--------|
| Views | YouTube Analytics | 500/video (avg) |
| Avg. watch time | YouTube Analytics | > 50% |
| Engagement rate | (Likes+Comments)/views | 5% |
| Subscriptions from video | YouTube Analytics | 1% of views |
| Click-through to website | YouTube cards/description | 2% |

---

## 6. Monthly Review Template

```markdown
# Marketing Report - [Month Year]

## Executive Summary
- MRR contribution: $___
- New customers: ___
- CAC: $___ (vs target $___)
- Top performing channel: _____

## Traffic & SEO
- Total visitors: ___ (↑/↓ ___%)
- Organic traffic: ___ (___% of total)
- Top landing pages: [list]
- Keyword movements: [summary]

## Social Media
- Follower growth: ___ (___%)
- Top posts: [links]
- Engagement rate: ___%

## Content Performance
- Blog posts published: ___
- Newsletter sent to: ___ subscribers
- Open rate: ___%, Click rate: ___%
- Videos published: ___, Total views: ___

## Lead Generation
- Lead magnet downloads: ___
- Demo requests: ___
- Free trials: ___
- Trial → paid: ___%

## Revenue
- New MRR: $___
- New customers: ___
- Churn MRR: $___
- ARPU: $___

## Insights & Actions
- What worked: ____
- What didn't: ____
- Next month focus: ____

## Metrics Dashboard Screenshots
[Attach screenshots]
```

---

## 7. Funnel Conversion Benchmarks

### Industry Standards (SaaS)
| Funnel Stage | Avg. Conversion | Mekong Target |
|--------------|-----------------|---------------|
| Visitor → Email capture | 1-3% | 2-4% |
| Email → Demo request | 10-20% | 15-25% |
| Demo → Trial | 50-70% | 60-80% |
| Trial → Paid | 2-8% | 4-6% |

### Mekong Funnel (Target)
```
1,000 visitors/month
  ↓ 2% (20)
Email captures
  ↓ 20% (4)
Demo requests
  ↓ 70% (3)
Free trials
  ↓ 50% (1.5)
Paying customers

CAC: $100-150 per customer
```

---

## 8. A/B Testing Framework

### Test Ideas
- **CTAs:** "Start Free Trial" vs "See Pricing" vs "Book Demo"
- **Headlines:** Vision-focused vs. Feature-focused vs. Benefit-focused
- **Lead magnets:** Ebook vs. Checklist vs. Video course
- **Email subject lines:** Question vs. Statement vs. Urgency
- **Pricing page:** Annual only vs. Monthly + Annual

### Test Process
1. Formulate hypothesis
2. Create variants (A vs B)
3. Run for 2-4 weeks or until statistical significance
4. Analyze results
5. Implement winner or iterate

### Success Criteria
- Statistical significance: 95% confidence
- Minimum sample size: 100 conversions
- Minimum detectable effect: 10%

---

## 9. Data Sources & Tracking Setup

### Required Tools
- **GA4:** Website analytics, conversion tracking
- **ConvertKit:** Newsletter, email automation
- **Ahrefs:** SEO ranking tracking
- **Stripe/Polar:** Revenue, customer data
- **CRM:** HubSpot or Pipedrive for lead tracking
- **Social platforms:** Native analytics

### UTM Parameters
```
Format: utm_source={platform}&utm_medium={content}&utm_campaign={theme}

Example:
utm_source=twitter&utm_medium=organic&utm_campaign=vision-series
utm_source=newsletter&utm_medium=weekly&utm_campaign=w25
```

### Conversion Events to Track
- Newsletter signup
- Lead magnet download
- Demo request
- Trial signup (Polar checkout initiated)
- Purchase completed
- Upgrade (Starter → Growth, etc.)

---

## 10. Monthly KPI Scorecard

| KPI | Target | Actual | Status | Notes |
|-----|--------|--------|--------|-------|
| Visitors | 5,000 | | | |
| Newsletter subs | 1,000 | | | |
| Open rate | 20% | | | |
| Click rate | 3% | | | |
| Trial signups | 100 | | | |
| Paid customers | 25 | | | |
| MRR | $3,000 | | | |
| CAC | $150 | | | |
| Twitter followers | 2,000 | | | |
| YouTube subs | 200 | | | |

**Status Key:** ✅ On track ⚠️ At risk ❌ Behind

---

*Last updated: June 20, 2026*  
*Next review: Monthly*  
*Owner: Marketing Manager*
