export interface CompanyProfile {
  name: string;
  stage: 'pre-seed' | 'seed' | 'series-a' | 'series-b' | 'growth';
  mrr: number;
  users: number;
  market: string;
  founded: number;
  industry?: 'saas' | 'marketplace' | 'fintech' | 'consumer' | 'enterprise';
  avgPrice?: number;
  addressablePct?: number;
  capturePct?: number;
}

export interface MarketSizing {
  tam: number;
  sam: number;
  som: number;
}

export interface PitchDeck {
  problem: string;
  solution: string;
  market: MarketSizing;
  traction: string;
  projections: YearProjection[];
  team: string;
  ask: string;
}

export interface KPISnapshot {
  mrr: number;
  growth: number;
  users: number;
  churn: number;
}

export interface YearProjection {
  year: number;
  mrr: number;
  users: number;
  revenue: number;
}

const AVG_PRICE_BY_STAGE: Record<string, number> = {
  'pre-seed': 50,
  seed: 100,
  'series-a': 200,
  'series-b': 500,
  growth: 1000,
};

const ADDRESSABLE_PCT: Record<string, number> = {
  saas: 0.15,
  marketplace: 0.1,
  fintech: 0.08,
  consumer: 0.05,
  enterprise: 0.12,
};

const CAPTURE_PCT: Record<string, number> = {
  'pre-seed': 0.01,
  seed: 0.02,
  'series-a': 0.05,
  'series-b': 0.08,
  growth: 0.15,
};

function formatUSD(n: number): string {
  if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  return `$${(n / 1_000).toFixed(0)}K`;
}

function calcMarket(profile: CompanyProfile): MarketSizing {
  const avgPrice = profile.avgPrice ?? AVG_PRICE_BY_STAGE[profile.stage];
  const industry = profile.industry ?? 'saas';
  const addressable = profile.addressablePct ?? ADDRESSABLE_PCT[industry] ?? 0.1;
  const capture = profile.capturePct ?? CAPTURE_PCT[profile.stage];

  // Market size proxy: 1M potential customers * avgPrice * 12 months
  const baseCustomers = 1_000_000;
  const tam = baseCustomers * avgPrice * 12;
  const sam = tam * addressable;
  const som = sam * capture;
  return { tam, sam, som };
}

function project3Years(profile: CompanyProfile): YearProjection[] {
  const growthRate = profile.stage === 'growth' ? 0.8 : profile.stage === 'series-b' ? 1.0 : 1.5;
  const results: YearProjection[] = [];
  let mrr = profile.mrr;
  let users = profile.users;
  const currentYear = new Date().getFullYear();

  for (let i = 1; i <= 3; i++) {
    mrr = mrr * (1 + growthRate / 12) ** 12;
    users = Math.round(users * (1 + growthRate / 12) ** 12);
    results.push({
      year: currentYear + i,
      mrr: Math.round(mrr),
      users,
      revenue: Math.round(mrr * 12),
    });
  }
  return results;
}

export class PitchGenerator {
  private profile: CompanyProfile | null = null;
  private deck: PitchDeck | null = null;

  generatePitchData(company: CompanyProfile): PitchDeck {
    this.profile = company;
    const market = calcMarket(company);
    const projections = project3Years(company);
    const arr = company.mrr * 12;

    this.deck = {
      problem: `${company.market} is inefficient, costly, and broken for modern businesses.`,
      solution: `${company.name} delivers an AI-native platform that solves ${company.market} at scale.`,
      market,
      traction: `${formatUSD(company.mrr)} MRR, ${company.users.toLocaleString()} users, founded ${company.founded}. ARR: ${formatUSD(arr)}.`,
      projections,
      team: `Founding team with deep domain expertise in ${company.market}.`,
      ask: this.calcAsk(company, market),
    };
    return this.deck;
  }

  private calcAsk(profile: CompanyProfile, market: MarketSizing): string {
    const askAmounts: Record<string, number> = {
      'pre-seed': 500_000,
      seed: 2_000_000,
      'series-a': 8_000_000,
      'series-b': 25_000_000,
      growth: 75_000_000,
    };
    const amount = askAmounts[profile.stage];
    const useOfFunds = profile.stage === 'pre-seed' || profile.stage === 'seed'
      ? 'product development and initial GTM'
      : 'sales, marketing, and international expansion';
    return `Raising ${formatUSD(amount)} to fund ${useOfFunds}. SOM target: ${formatUSD(market.som)}.`;
  }

  updateFromKPIs(kpis: KPISnapshot): void {
    if (!this.profile || !this.deck) return;
    this.profile = { ...this.profile, mrr: kpis.mrr, users: kpis.users };
    const arr = kpis.mrr * 12;
    this.deck.traction = `${formatUSD(kpis.mrr)} MRR (+${(kpis.growth * 100).toFixed(1)}% MoM), ${kpis.users.toLocaleString()} users, ${(kpis.churn * 100).toFixed(1)}% churn. ARR: ${formatUSD(arr)}.`;
    this.deck.projections = project3Years(this.profile);
    this.deck.market = calcMarket(this.profile);
  }

  exportJSON(): string {
    if (!this.deck) throw new Error('No pitch deck generated yet. Call generatePitchData() first.');
    return JSON.stringify(this.deck, null, 2);
  }

  generateOneLiner(): string {
    if (!this.profile || !this.deck) throw new Error('No pitch deck generated yet.');
    const market = calcMarket(this.profile);
    return `${this.profile.name} is a ${this.profile.stage} ${this.profile.industry ?? 'SaaS'} company solving ${this.profile.market} — ${formatUSD(this.profile.mrr)} MRR, targeting a ${formatUSD(market.sam)} SAM.`;
  }
}
