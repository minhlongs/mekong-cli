---
description: IPO day execution — pricing night to bell ringing, first-trade ops
allowed-tools: Read, Write
---

# /founder ipo-day — IPO Execution Command

## USAGE
```
/founder ipo-day [--t-minus <days>] [--checklist | --pricing | --ceremony]
```

## T-MINUS 1 DAY: PRICING NIGHT

```
22:00 — PRICING CALL WITH BANKERS

Who's on the call:
  CEO, CFO, General Counsel
  Lead banker (book-running manager)
  Exchange representative

The call agenda:
  1. Final order book review
     "Book is {n}x subscribed at ${price}"
  
  2. Pricing decision
     Option A: Price at top of range
     Option B: Price above range (if demand warrants)
     Option C: Price in range
     
     FORMULA:
       Underprice: investors happy, founder leaves money on table
       Overprice: stock drops, bad headlines, unhappy investors
       Target: 10-20% first-day pop = well-priced IPO
  
  3. Allocation finalization
     Top accounts confirmed
     Final share distribution locked
  
  4. Trading ticker confirmed: {TICKER} on {EXCHANGE}

23:00 — AFTER PRICING

  □ Final S-1 amendment filed with SEC
  □ Press release drafted and ready (embargo until open)
  □ Employee communications ready
  □ Family + key stakeholders notified personally
  □ Social media post drafted (send after open)
  □ Get some sleep (probably won't happen)

PRICING NEGOTIATION WITH BANKERS:
  Bankers want: conservative price = easy oversubscription = safe
  Founders want: highest price = max proceeds + valuation
  
  Counter-pressure:
  "Our long-term holders are expecting ${range}. If demand
   supports it at {n}x coverage, I want to be at the top.
   What's the downside scenario analysis?"
  
  Watch for: bankers sandbagging on demand to justify lower price
  Your tool: /founder cap-table --exit (IPO price × total shares)
```

## IPO DAY TIMELINE

```
05:00 — WAKE UP

  □ Check overnight news for any market disruptions
  □ Review banker update on opening demand
  □ Brief final remarks for any morning TV/press

06:00 — PRESS EMBARGO LIFTS

  □ Press release goes live
  □ CEO statement to all employees (email prepared)
  □ Social media posts go live (LinkedIn, Twitter)
  □ Customer notification (if relevant)

07:00 — ARRIVE AT EXCHANGE

  □ NASDAQ: 4 Times Square, NYC
  □ NYSE: 11 Wall Street, NYC
  □ HoSE: HCMC or Hanoi exchange floor
  
  Who comes:
  □ Founding team
  □ Key employees (flight organized in advance)
  □ Early investors (invite the ones who helped)
  □ Key customers (optional but powerful signal)
  □ Family (optional but emotional moment)

09:00 — MEDIA INTERVIEWS

  □ CNBC/Bloomberg pre-market interview
  □ Stay on message: company mission + growth story
  □ Never comment on valuation or target price
  □ Script: "We're focused on executing our mission,
    the market will reflect our results over time."

09:28 — NASDAQ OPENING CEREMONY

  □ 2-minute remarks at podium
  □ Ring the opening bell (NASDAQ) or closing bell (NYSE)
  □ Team photo on the balcony
  □ This moment will be in every company history

SPEECH TEMPLATE (2 minutes, memorize):
  "Thank you to {key early believers}.
   
   {N} years ago, we started {company} because {why}.
   
   Today we're public because our customers believed in us.
   {Customer metric that proves the point}.
   
   But this is not the finish line — this is the starting gun
   for our next chapter.
   
   To our team: you did this. To our customers: thank you.
   To our new public investors: we will earn your trust
   every quarter.
   
   {Ticker}: {company name} is now public. Let's build."

09:30 — MARKET OPENS

  □ Watch the first trades
  □ Target: 10-20% above IPO price at open
  □ Do NOT obsessively watch the price (it's volatile day 1)
  □ Stabilization agent (banker) will manage large swings

FIRST DAY TRADING:
  Market maker ensures orderly trading
  Greenshoe option: bankers can buy back up to 15% extra
    shares if price drops (price support mechanism)
  IPO day is often highest volume day

12:00 — EMPLOYEE CELEBRATION

  □ All-hands video call to remote team
  □ Champagne if team is together
  □ Acknowledge everyone by name who built this
  □ ESOP cliff/vest: many employees vest at IPO — celebrate that

16:00 — MARKET CLOSE

  □ Final price noted in company history
  □ Market cap calculated
  □ Founder stake value calculated
  □ Investor update email (brief, professional)

FIRST DAY CLOSE EMAIL TO INVESTORS:
  Subject: {TICKER} First Trading Day — Note from CEO
  
  "Today {Company} began trading as a public company.
   
   We priced at ${X} and closed at ${Y} — a reflection of
   the market's view of our potential.
   
   What hasn't changed: our mission, our team, our focus on
   {North Star metric}. What has changed: we now have
   the resources and public accountability to execute at scale.
   
   We'll speak again on {earnings date} with Q{n} results.
   Thank you for joining us on this journey."
```

## POST-IPO WEEK 1 CHECKLIST

```
DAY 2-5:
  □ Analyst initiation reports start coming (2-4 weeks post-IPO)
  □ Begin quiet period compliance (NO talking about stock price)
  □ Set up insider trading policy + 10b5-1 plan
  □ Board update on day-1 results
  □ Begin quarterly reporting calendar setup

LOCKUP REMINDER:
  □ 180-day lockup: insiders can't sell until {date}
  □ Brief all insiders: NO selling, NO commentary
  □ /founder lockup-expiry (plan strategy for lockup end)
  
QUIET PERIOD:
  □ 40 days post-IPO: no forward guidance, no new statements
  □ Only speak through official filings and press releases
  □ Social media: company news OK, financial commentary NOT
```

## METRICS TO CELEBRATE (not publicly)

```
FOUNDER MILESTONE CALCULATOR:

  IPO price:           ${price}
  Founder shares:      {n}M
  Founder value:       ${price × shares}M
  
  After lockup (180d): {projected_value based on forward multiple}
  
  vs Bootstrap start:  {journey from $0 to this}
  
  Years to get here:   {n}
  Team who made it:    {n} people
  
  First investor check: ${first_check}
  IPO market cap:       ${cap}B
  MULTIPLE:             {cap / first_check}x

LEGACY STATEMENT (for your biography):
  "{Company} went public on {date} at {market_cap},
   making it one of {Vietnam/SEA/global}'s
   most valuable technology companies."
```

## OUTPUT

```
✅ IPO Day Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 .mekong/ipo/ipo-day/
  ✓ pricing-night-agenda.md
  ✓ day-of-timeline.md
  ✓ bell-speech.md
  ✓ employee-announcement.md
  ✓ press-release.md
  ✓ day-1-investor-note.md
  ✓ week-1-checklist.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -3 (balance: {remaining})

AFTER THIS: /founder public-co begins.
The real work starts now.
Public companies don't get to rest.
```
