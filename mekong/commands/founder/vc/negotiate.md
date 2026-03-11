---
description: VC negotiation playbook — BATNA tactics, counter-offers, pressure responses, closing
allowed-tools: Read, Write
---

# /founder negotiate — VC Negotiation Intelligence

## USAGE
```
/founder negotiate [--term-sheet <file>] [--stage <prep|live|closing>]
```

## BƯỚC 0 — SCAN
```
□ Đọc .mekong/raise/term-sheet-analysis.md   → trap list từ /founder term-sheet
□ Đọc .mekong/raise/cap-table.json            → current ownership
□ Đọc .mekong/raise/bootstrap-plan.md         → BATNA strength
□ Đọc .mekong/reports/ (latest)               → traction (negotiating power)
```

## BƯỚC 1 — BATNA ASSESSMENT

**Trước khi vào phòng đàm phán, biết rõ BATNA của mình:**

```
BATNA STRENGTH CALCULATOR:

Strong BATNA (negotiate aggressively):
  □ MRR > $25K growing > 15%/mo
  □ 2+ competing term sheets
  □ 18+ months runway without this round
  □ Revenue-based financing approved
  □ Profitable or path to profit clear

Weak BATNA (negotiate carefully, bootstrap first):
  □ MRR < $5K
  □ < 3 months runway
  □ No other investors interested
  □ Product not launched

RULE: Weak BATNA = don't negotiate yet, go back and build.
Strong BATNA = negotiate from confidence, can walk away.

YOUR BATNA SCORE: {calculated from company.json + reports}
STRATEGY: {AGGRESSIVE / BALANCED / CAREFUL}
```

## BƯỚC 2 — NEGOTIATION PREP

```
FILE: .mekong/raise/negotiation-prep.md

YOUR WALK-AWAY LINES (know these BEFORE meeting):
  Valuation floor : $___M pre-money (below this = walk)
  Max dilution    : ___% (above this = walk)
  Board config    : minimum {n} founder seats
  Liquidation     : non-participating only, hard line
  Option pool     : post-money only, hard line

YOUR TARGET (what you actually want):
  Valuation target: $___M pre-money
  Investment      : $___M
  Dilution        : ___%
  Board           : {config}

THEIR INTERESTS (use in negotiation):
  □ Fund timeline: need to deploy capital by {quarter}
  □ Portfolio fit: your company helps their narrative
  □ FOMO: other funds looking at you
  □ Fund size: small fund = need large % = more aggressive
    large fund = can afford smaller % = more flexible

INFORMATION LEVERAGE:
  Real traction data to show:
    MRR: ${n} ({pct}% MoM growth)
    Revenue: ${n} total
    Growth rate: top {pct}% of companies at our stage
  
  Social proof:
    "{notable customer}" uses our product
    "Featured in {publication}"
    "Recommended by {founder they respect}"
```

## BƯỚC 3 — LIVE NEGOTIATION SCRIPTS

### OPENING THE NEGOTIATION

```
NEVER react to their first offer. Always counter.

Their first offer is not their best offer.
Rule: First offer is typically 20-30% below their real number.

RECEIVING TERM SHEET:
  "Thank you for the term sheet. We're reviewing it carefully
   and will get back to you by {date}."
  
  Never: "This looks great!" (killed your leverage)
  Never: "We need to think about it" without deadline
  Always: give yourself 5-7 days to review

ASKING FOR SPACE:
  "We want to make a thoughtful decision. 
   We'll have our response by Friday."
  (Use the time to: run /founder term-sheet, consult lawyer,
   shop to other investors)
```

### COUNTERING SPECIFIC TERMS

```
VALUATION COUNTER:
  Their offer: $8M pre-money
  Your counter: $12M pre-money
  
  Script:
  "We appreciate the offer. Based on our current metrics —
   ${mrr} MRR growing ${growth}% monthly — and comparable
   rounds in our sector, we believe $12M pre is more appropriate.
   We have conviction in our trajectory and we're talking to
   {n} other investors who are aligned on this range.
   Can you meet us at $12M?"
  
  IF they push back:
  "Help me understand the valuation model you're using.
   I want to find a number that works for both of us."
  (Make them justify their number — puts them on defense)

LIQUIDATION PREFERENCE COUNTER:
  Their offer: 1x participating preferred
  Your counter: 1x non-participating
  
  Script:
  "On the liquidation preference — we'd like to move to
   non-participating preferred. Here's our reasoning:
   participating preferred actually misaligns our incentives.
   At a $30M exit, we'd have less incentive to optimize for
   max value. Non-participating keeps us fully aligned.
   We've modeled this and can show you the numbers."
  
  IF they won't move:
  "If participation is important to you, can we add a cap?
   Once you've returned 3x, participation converts to common.
   That protects your downside while preserving our upside."

BOARD CONTROL COUNTER:
  Their offer: 2 investor seats, 1 founder, 1 independent
  Your counter: 2 founder, 1 investor, 1 independent
  
  Script:
  "We'd like to maintain founder control on the board.
   At seed stage, we're still learning what works.
   We'd like 2 founder seats and 1 investor seat.
   We can add a second investor seat when we raise Series A."
  
  The frame: "Board control = founder accountability to execute"
  
  IF they push: 2+2+1 (2 founders, 2 investors, 1 independent)
  "Let's make it balanced: 2 founders, 2 investors, 1 independent
   selected by mutual consent. That's true partnership."

OPTION POOL COUNTER:
  Their offer: 15% option pool, pre-money
  Your counter: 10% option pool, post-money
  
  Script:
  "On the option pool — we'd prefer to create it post-closing.
   Pre-money option pools are an implicit valuation cut.
   At 15% pre-money on $8M, that's actually a $6.8M effective pre.
   Post-money, post-closing at 10% is standard for our stage."
  
  The math: show them the /founder cap-table model
  "Here's the dilution impact either way. Post-money 10% 
   puts us both in a better position."

NO-SHOP / EXCLUSIVITY COUNTER:
  Their offer: 45-day exclusivity
  Your counter: 21 days
  
  Script:
  "45 days is a long no-shop. We're a fast-moving company.
   Can we agree on 21 days with a good-faith milestone:
   if diligence has specific blockers, we'll extend.
   Otherwise 21 days is plenty to close."
```

### HANDLING PRESSURE TACTICS

```
TACTIC: "We need an answer by Friday"
  Reality: artificial urgency is almost always fake
  Response: 
  "We want to work with you but we make considered decisions.
   We'll have our answer by {your date, 3-5 days later}.
   If that doesn't work for your timeline, let's talk about why."
  
  Never fold to fake urgency. If they pull the offer:
  they were not serious partners anyway.

TACTIC: "We have 2 other companies we're looking at"
  Reality: may be true, may not be
  Response:
  "That's fine — we're talking to a few investors ourselves.
   Let's focus on whether we're the right fit for each other."
  
  Counter-FOMO: mention your other conversations casually
  "We're actually comparing a couple of terms right now..."

TACTIC: "This is our standard term sheet, we don't change it"
  Reality: every term sheet is negotiable
  Response:
  "We respect that you have a standard — and we want to work
   with you. But {specific clause} doesn't work for our situation.
   Can we find a creative structure that respects your standard
   while addressing our concern?"
  
  Alternatively:
  "Our lawyer flagged {clause} as unusual for our stage.
   Can you help me understand the intent behind it?"
  
  (Asking "what's the intent?" often unlocks flexibility)

TACTIC: "All our portfolio companies have these terms"
  Reality: you are not their other portfolio companies
  Response:
  "We're different situations at different stages.
   {Specific clause} would misalign our incentives in our case
   because {specific reason}. Can we address this specifically?"

TACTIC: "You're early for this valuation"
  Response:
  "We're growing at {pct}% monthly. At this rate, in 6 months
   we'll clearly justify this valuation — and we'll be raising
   at a higher price. We think {valuation} reflects where we
   are in that trajectory. If you need more proof points,
   let's talk about a milestone-based structure."
```

### CLOSING THE DEAL

```
WHEN TO SIGN:
  □ All MUST FIX issues resolved (from /founder term-sheet)
  □ Lawyer has reviewed final documents
  □ Cap table modeled post-close (from /founder cap-table)
  □ You can execute on the milestone this round is for
  □ You genuinely trust this partner (gut check matters)

WHEN TO WALK:
  □ Any MUST FIX issue not resolved
  □ Participating liquidation pref they won't remove
  □ Board majority for investor post-seed
  □ Full ratchet anti-dilution
  □ You feel pressured to sign without full understanding
  □ Your BATNA is better than this deal

FINAL SIGN CHECKLIST:
  □ Term sheet signed by all parties
  □ Wire instructions verified (fraud risk at closing)
  □ Cap table updated in .mekong/raise/cap-table.json
  □ All representations confirmed accurate
  □ First board meeting scheduled
  □ Lawyer relationship established for future rounds
```

## OUTPUT

```
✅ Negotiation Playbook Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BATNA strength: {STRONG / MODERATE / WEAK}
Negotiation stance: {AGGRESSIVE / BALANCED}

📁 .mekong/raise/
  ✓ negotiation-prep.md
  ✓ walk-away-lines.md
  ✓ counter-scripts.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💳 MCU: -3 (balance: {remaining})

CORE RULE:
  "The founder who can walk away owns the room."
  Build that BATNA first.
  Then negotiate every term.
```
