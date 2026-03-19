import type { CompanyProfile } from './pitch-generator.js';

export interface Financials {
  annualRevenue: number;
  growthRate: number;
  ebitdaMargin: number;
  discountRate: number;
}

export interface ExitStrategy {
  type: 'ipo' | 'acquisition' | 'merger';
  timeline: string;
  estimatedValue: number;
  probability: number;
}

export interface PotentialBuyer {
  name: string;
  type: 'strategic' | 'pe' | 'spac';
  fitScore: number;
}

export interface TimelineStep {
  phase: string;
  duration: string;
  description: string;
}

const REVENUE_MULTIPLES: Record<string, [number, number]> = {
  saas: [10, 15],
  marketplace: [5, 8],
  fintech: [8, 12],
  consumer: [3, 6],
  enterprise: [7, 12],
};

const STRATEGIC_BUYERS: Record<string, PotentialBuyer[]> = {
  saas: [
    { name: 'Salesforce', type: 'strategic', fitScore: 85 },
    { name: 'ServiceNow', type: 'strategic', fitScore: 78 },
    { name: 'Vista Equity Partners', type: 'pe', fitScore: 72 },
  ],
  marketplace: [
    { name: 'Amazon', type: 'strategic', fitScore: 82 },
    { name: 'Shopify', type: 'strategic', fitScore: 79 },
    { name: 'Thoma Bravo', type: 'pe', fitScore: 70 },
  ],
  fintech: [
    { name: 'Stripe', type: 'strategic', fitScore: 88 },
    { name: 'PayPal', type: 'strategic', fitScore: 75 },
    { name: 'FTV Capital', type: 'pe', fitScore: 68 },
  ],
};

const DEFAULT_BUYERS: PotentialBuyer[] = [
  { name: 'Industry Leader A', type: 'strategic', fitScore: 70 },
  { name: 'Private Equity Fund B', type: 'pe', fitScore: 65 },
  { name: 'SPAC Vehicle C', type: 'spac', fitScore: 55 },
];

export class ExitEngine {
  calculateValuation(method: 'revenue-multiple' | 'dcf', financials: Financials): number {
    if (method === 'revenue-multiple') {
      const industry = 'saas'; // default; caller can set via subclass
      const [low, high] = REVENUE_MULTIPLES[industry] ?? [5, 8];
      const multiple = low + (high - low) * Math.min(financials.growthRate, 1);
      return Math.round(financials.annualRevenue * multiple);
    }

    // DCF: 5-year projection + terminal value
    const years = 5;
    let dcf = 0;
    let revenue = financials.annualRevenue;
    for (let i = 1; i <= years; i++) {
      revenue *= 1 + financials.growthRate;
      const fcf = revenue * financials.ebitdaMargin;
      dcf += fcf / (1 + financials.discountRate) ** i;
    }
    // Terminal value at 2% perpetual growth
    const terminalFCF = revenue * financials.ebitdaMargin;
    const terminalValue = terminalFCF * (1 + 0.02) / (financials.discountRate - 0.02);
    dcf += terminalValue / (1 + financials.discountRate) ** years;
    return Math.round(dcf);
  }

  recommendStrategy(company: CompanyProfile): ExitStrategy {
    const arr = company.mrr * 12;

    if (arr >= 50_000_000 && (company.stage === 'growth' || company.stage === 'series-b')) {
      return { type: 'ipo', timeline: '18-24 months', estimatedValue: arr * 12, probability: 0.65 };
    }
    if (arr >= 10_000_000) {
      return { type: 'acquisition', timeline: '12-18 months', estimatedValue: arr * 10, probability: 0.75 };
    }
    return { type: 'merger', timeline: '6-12 months', estimatedValue: arr * 6, probability: 0.55 };
  }

  matchBuyers(profile: CompanyProfile): PotentialBuyer[] {
    const industry = profile.industry ?? 'saas';
    const buyers = STRATEGIC_BUYERS[industry] ?? DEFAULT_BUYERS;
    // Sort by fit score descending
    return [...buyers].sort((a, b) => b.fitScore - a.fitScore);
  }

  generateExitTimeline(strategy: ExitStrategy): TimelineStep[] {
    if (strategy.type === 'ipo') {
      return [
        { phase: 'Preparation', duration: '3-6 months', description: 'Audit financials, hire I-banks, build S-1 narrative' },
        { phase: 'Roadshow', duration: '2-4 weeks', description: 'Investor meetings across major financial centers' },
        { phase: 'Pricing', duration: '1 week', description: 'Final pricing, bookbuild, and allocation' },
        { phase: 'Lock-up', duration: '6 months', description: 'Post-IPO lock-up period for insiders' },
      ];
    }
    if (strategy.type === 'acquisition') {
      return [
        { phase: 'Outreach', duration: '1-2 months', description: 'Engage M&A advisors, initiate buyer conversations' },
        { phase: 'Due Diligence', duration: '2-3 months', description: 'Data room review, legal, financial, tech audits' },
        { phase: 'Negotiation', duration: '1-2 months', description: 'LOI, definitive agreement, regulatory approvals' },
        { phase: 'Integration', duration: '6-12 months', description: 'Systems, team, and product integration post-close' },
      ];
    }
    return [
      { phase: 'Partner Identification', duration: '1-2 months', description: 'Identify merger candidates with strategic fit' },
      { phase: 'Term Negotiation', duration: '1-2 months', description: 'Merger ratio, governance, and combined entity structure' },
      { phase: 'Regulatory Approval', duration: '2-4 months', description: 'Antitrust and shareholder approvals' },
      { phase: 'Combined Operations', duration: '6-12 months', description: 'Operational synergies realization' },
    ];
  }
}
