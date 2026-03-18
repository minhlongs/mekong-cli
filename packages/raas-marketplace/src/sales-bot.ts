import type { Product } from "./catalog.js";

export interface Lead {
  name: string;
  email: string;
  company: string;
  size: number; // headcount
  budget: number; // USD/mo
  useCase: string;
}

export interface LeadScore {
  score: number; // 0-100
  tier: "starter" | "pro" | "enterprise";
  reasoning: string;
}

export interface FollowUpEmail {
  subject: string;
  body: string;
  sendAfterDays: number;
}

export class SalesBot {
  qualifyLead(lead: Lead): LeadScore {
    let score = 0;
    const reasons: string[] = [];

    // Company size (max 40 pts)
    if (lead.size >= 500) { score += 40; reasons.push("large enterprise"); }
    else if (lead.size >= 50) { score += 25; reasons.push("mid-market"); }
    else if (lead.size >= 10) { score += 15; reasons.push("small business"); }
    else { score += 5; reasons.push("solo/micro"); }

    // Budget fit (max 40 pts)
    if (lead.budget >= 400) { score += 40; reasons.push("enterprise budget"); }
    else if (lead.budget >= 100) { score += 25; reasons.push("pro budget"); }
    else if (lead.budget >= 40) { score += 15; reasons.push("starter budget"); }
    else { score += 5; reasons.push("limited budget"); }

    // Use case specificity (max 20 pts)
    const useCaseWords = lead.useCase.split(" ").length;
    if (useCaseWords >= 10) { score += 20; reasons.push("clear use case"); }
    else if (useCaseWords >= 5) { score += 12; reasons.push("partial use case"); }
    else { score += 5; reasons.push("vague use case"); }

    const tier = this.getRecommendedTier(lead) as LeadScore["tier"];
    return { score, tier, reasoning: reasons.join(", ") };
  }

  generateProposal(lead: Lead, products: Product[]): string {
    const tier = this.getRecommendedTier(lead);
    const product = products.find((p) => p.tier === tier && p.active);
    if (!product) return `# Proposal for ${lead.company}\n\nNo matching product found.`;

    return `# Custom Proposal for ${lead.company}

**Prepared for:** ${lead.name} <${lead.email}>
**Company Size:** ${lead.size} people
**Monthly Budget:** $${lead.budget}

## Recommended Plan: ${product.name} ($${product.basePriceUsd}/mo)

${product.description}

### What You Get
${product.features.map((f) => `- ${f}`).join("\n")}

### Why This Fits ${lead.company}
Based on your use case — "${lead.useCase}" — the ${product.name} plan gives you everything you need to ship fast without overpaying.

### Next Steps
1. Start your 14-day free trial
2. Book an onboarding call: [calendly.com/openclaw/onboard](https://calendly.com/openclaw/onboard)
3. Questions? Reply to this email

**Get started:** [openclaw.io/checkout?product=${product.id}](https://openclaw.io/checkout?product=${product.id})
`;
  }

  generateFollowUpSequence(lead: Lead): FollowUpEmail[] {
    const tier = this.getRecommendedTier(lead);
    return [
      {
        subject: `${lead.name}, quick question about ${lead.company}'s AI stack`,
        body: `Hi ${lead.name},\n\nSaw you checked out OpenClaw — curious what you're trying to automate at ${lead.company}.\n\nOur ${tier} plan might be a great fit. Want a 15-min walk-through?\n\n— OpenClaw Team`,
        sendAfterDays: 1,
      },
      {
        subject: `3 things teams like ${lead.company} automate with OpenClaw`,
        body: `Hi ${lead.name},\n\n1. Lead qualification at scale\n2. Content & proposal generation\n3. Sales follow-up sequences (like this one!)\n\nAll on ${tier} plan for $${tier === "starter" ? 49 : tier === "pro" ? 149 : 499}/mo.\n\nTry free for 14 days → https://openclaw.io/trial`,
        sendAfterDays: 4,
      },
      {
        subject: `Last chance — your OpenClaw trial offer expires soon`,
        body: `Hi ${lead.name},\n\nJust wanted to make sure you didn't miss this.\n\nIf now isn't the right time, no worries — just reply and I'll check back in a month.\n\nOtherwise, grab your trial: https://openclaw.io/trial\n\n— OpenClaw Team`,
        sendAfterDays: 10,
      },
    ];
  }

  getRecommendedTier(lead: Lead): string {
    if (lead.size >= 200 || lead.budget >= 400) return "enterprise";
    if (lead.size >= 20 || lead.budget >= 100) return "pro";
    return "starter";
  }
}
