import { describe, it, expect } from 'vitest';
import { PitchGenerator } from './pitch-generator.js';
import { DataRoom } from './data-room.js';
import { ComplianceEngine } from './iso-compliance.js';
import { ExitEngine } from './exit-engine.js';
import { BoardMeeting } from './board-meeting.js';
import type { CompanyProfile, KPISnapshot } from './pitch-generator.js';

const SAMPLE_COMPANY: CompanyProfile = {
  name: 'OpenClaw',
  stage: 'seed',
  mrr: 50_000,
  users: 1_200,
  market: 'AI-powered business automation',
  founded: 2023,
  industry: 'saas',
};

// --- PitchGenerator ---

describe('PitchGenerator', () => {
  it('generates pitch deck with all required fields', () => {
    const gen = new PitchGenerator();
    const deck = gen.generatePitchData(SAMPLE_COMPANY);
    expect(deck.problem).toBeTruthy();
    expect(deck.solution).toBeTruthy();
    expect(deck.market.tam).toBeGreaterThan(0);
    expect(deck.market.sam).toBeGreaterThan(0);
    expect(deck.market.som).toBeGreaterThan(0);
    expect(deck.projections).toHaveLength(3);
    expect(deck.traction).toContain('MRR');
  });

  it('market hierarchy: TAM > SAM > SOM', () => {
    const gen = new PitchGenerator();
    const deck = gen.generatePitchData(SAMPLE_COMPANY);
    expect(deck.market.tam).toBeGreaterThan(deck.market.sam);
    expect(deck.market.sam).toBeGreaterThan(deck.market.som);
  });

  it('projections increase year over year', () => {
    const gen = new PitchGenerator();
    const deck = gen.generatePitchData(SAMPLE_COMPANY);
    const [y1, y2, y3] = deck.projections;
    expect(y2.mrr).toBeGreaterThan(y1.mrr);
    expect(y3.mrr).toBeGreaterThan(y2.mrr);
  });

  it('updateFromKPIs refreshes traction', () => {
    const gen = new PitchGenerator();
    gen.generatePitchData(SAMPLE_COMPANY);
    const kpis: KPISnapshot = { mrr: 80_000, growth: 0.15, users: 2_000, churn: 0.02 };
    gen.updateFromKPIs(kpis);
    const json = JSON.parse(gen.exportJSON());
    expect(json.traction).toContain('15.0%');
  });

  it('exportJSON returns valid JSON', () => {
    const gen = new PitchGenerator();
    gen.generatePitchData(SAMPLE_COMPANY);
    expect(() => JSON.parse(gen.exportJSON())).not.toThrow();
  });

  it('exportJSON throws before generatePitchData', () => {
    const gen = new PitchGenerator();
    expect(() => gen.exportJSON()).toThrow();
  });

  it('generateOneLiner contains company name', () => {
    const gen = new PitchGenerator();
    gen.generatePitchData(SAMPLE_COMPANY);
    expect(gen.generateOneLiner()).toContain('OpenClaw');
  });
});

// --- DataRoom ---

describe('DataRoom', () => {
  it('addDocument and listDocuments round-trips', () => {
    const room = new DataRoom();
    room.addDocument({ name: 'Articles', category: 'legal', content: 'text', uploadedAt: new Date() });
    room.addDocument({ name: 'P&L', category: 'financial', content: 'numbers', uploadedAt: new Date() });
    expect(room.listDocuments()).toHaveLength(2);
    expect(room.listDocuments('legal')).toHaveLength(1);
    expect(room.listDocuments('legal')[0].name).toBe('Articles');
  });

  it('listDocuments with unknown category returns empty', () => {
    const room = new DataRoom();
    expect(room.listDocuments('team')).toHaveLength(0);
  });

  it('generateCapTable computes percentages correctly', () => {
    const room = new DataRoom();
    const cap = room.generateCapTable([
      { name: 'Alice', shares: 600, type: 'founder' },
      { name: 'Bob', shares: 300, type: 'investor' },
      { name: 'Carol', shares: 100, type: 'employee' },
    ]);
    expect(cap.totalShares).toBe(1000);
    expect(cap.shareholders[0].percentage).toBeCloseTo(60);
    expect(cap.breakdown.founder.percentage).toBeCloseTo(60);
    expect(cap.breakdown.investor.percentage).toBeCloseTo(30);
    expect(cap.breakdown.employee.percentage).toBeCloseTo(10);
  });

  it('generateCapTable throws on zero shares', () => {
    const room = new DataRoom();
    expect(() => room.generateCapTable([])).toThrow('zero');
  });

  it('generateSAFE contains investor name and valuation cap', () => {
    const room = new DataRoom();
    const safe = room.generateSAFE('Sequoia Capital', 500_000, 5_000_000);
    expect(safe).toContain('Sequoia Capital');
    expect(safe).toContain('$5.00M');
    expect(safe).toContain('SAFE');
  });

  it('generateTermSheet contains priced-round details', () => {
    const room = new DataRoom();
    const ts = room.generateTermSheet({ investor: 'a16z', amount: 3_000_000, valuation: 12_000_000, type: 'priced' });
    expect(ts).toContain('a16z');
    expect(ts).toContain('$12.00M');
    expect(ts).toContain('Observer seat');
  });
});

// --- ComplianceEngine ---

describe('ComplianceEngine', () => {
  it('auditISO27001 returns 14 findings', () => {
    const engine = new ComplianceEngine();
    const result = engine.auditISO27001();
    expect(result.findings).toHaveLength(14);
    expect(result.standard).toContain('27001');
  });

  it('auditISO9001 score is within bounds', () => {
    const engine = new ComplianceEngine();
    const result = engine.auditISO9001();
    expect(result.score).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(result.maxScore);
  });

  it('auditSOC2 returns 5 findings', () => {
    const engine = new ComplianceEngine();
    const result = engine.auditSOC2();
    expect(result.findings).toHaveLength(5);
  });

  it('checkGDPR returns array with regulation field', () => {
    const engine = new ComplianceEngine();
    const checks = engine.checkGDPR();
    expect(checks.length).toBeGreaterThan(0);
    checks.forEach((c) => expect(c.regulation).toBe('GDPR'));
  });

  it('checkCCPA contains opt-out check', () => {
    const engine = new ComplianceEngine();
    const checks = engine.checkCCPA();
    const optOut = checks.find((c) => c.requirement.toLowerCase().includes('do not sell'));
    expect(optOut).toBeDefined();
  });

  it('generateComplianceReport is a non-empty string with markdown headers', () => {
    const engine = new ComplianceEngine();
    const report = engine.generateComplianceReport();
    expect(report).toContain('# Compliance Report');
    expect(report).toContain('ISO 27001');
    expect(report).toContain('GDPR');
    expect(report).toContain('CCPA');
  });
});

// --- ExitEngine ---

describe('ExitEngine', () => {
  const financials = { annualRevenue: 5_000_000, growthRate: 1.2, ebitdaMargin: 0.2, discountRate: 0.15 };

  it('calculateValuation revenue-multiple returns positive number', () => {
    const engine = new ExitEngine();
    const val = engine.calculateValuation('revenue-multiple', financials);
    expect(val).toBeGreaterThan(0);
  });

  it('calculateValuation dcf returns positive number', () => {
    const engine = new ExitEngine();
    const val = engine.calculateValuation('dcf', financials);
    expect(val).toBeGreaterThan(0);
  });

  it('recommendStrategy returns ipo for large growth company', () => {
    const engine = new ExitEngine();
    const bigCo: CompanyProfile = { ...SAMPLE_COMPANY, stage: 'growth', mrr: 5_000_000 };
    const strategy = engine.recommendStrategy(bigCo);
    expect(strategy.type).toBe('ipo');
    expect(strategy.probability).toBeGreaterThan(0);
  });

  it('recommendStrategy returns merger for early company', () => {
    const engine = new ExitEngine();
    const strategy = engine.recommendStrategy(SAMPLE_COMPANY); // mrr=50k
    expect(strategy.type).toBe('merger');
  });

  it('matchBuyers returns sorted by fitScore descending', () => {
    const engine = new ExitEngine();
    const buyers = engine.matchBuyers(SAMPLE_COMPANY);
    expect(buyers.length).toBeGreaterThan(0);
    for (let i = 1; i < buyers.length; i++) {
      expect(buyers[i - 1].fitScore).toBeGreaterThanOrEqual(buyers[i].fitScore);
    }
  });

  it('generateExitTimeline ipo returns 4 phases', () => {
    const engine = new ExitEngine();
    const strategy = engine.recommendStrategy({ ...SAMPLE_COMPANY, stage: 'growth', mrr: 5_000_000 });
    const timeline = engine.generateExitTimeline(strategy);
    expect(timeline).toHaveLength(4);
    timeline.forEach((step) => {
      expect(step.phase).toBeTruthy();
      expect(step.duration).toBeTruthy();
      expect(step.description).toBeTruthy();
    });
  });
});

// --- BoardMeeting ---

describe('BoardMeeting', () => {
  it('generateAgenda returns 10 standard items', () => {
    const bm = new BoardMeeting();
    const agenda = bm.generateAgenda('2026-03-18');
    expect(agenda.date).toBe('2026-03-18');
    expect(agenda.items).toHaveLength(10);
  });

  it('generateKPIDashboard contains key metrics', () => {
    const bm = new BoardMeeting();
    const kpis: KPISnapshot = { mrr: 120_000, growth: 0.12, users: 3_000, churn: 0.015 };
    const dashboard = bm.generateKPIDashboard(kpis);
    expect(dashboard).toContain('MRR');
    expect(dashboard).toContain('ARR');
    expect(dashboard).toContain('12.0%');
  });

  it('recordMinutes stores minutes retrievable via getMinutes', () => {
    const bm = new BoardMeeting();
    bm.recordMinutes({
      date: '2026-03-18',
      attendees: ['Alice', 'Bob'],
      decisions: ['Approve budget'],
      actionItems: [{ task: 'Send deck', owner: 'Alice', due: '2026-03-25' }],
    });
    expect(bm.getMinutes()).toHaveLength(1);
    expect(bm.getMinutes()[0].decisions[0]).toBe('Approve budget');
  });

  it('generateInvestorUpdate contains period and decisions', () => {
    const bm = new BoardMeeting();
    bm.recordMinutes({
      date: '2026-03-18',
      attendees: ['CEO'],
      decisions: ['Proceed with Series A'],
      actionItems: [],
    });
    const update = bm.generateInvestorUpdate('March 2026');
    expect(update).toContain('March 2026');
    expect(update).toContain('Proceed with Series A');
  });

  it('generateInvestorUpdate with no minutes falls back gracefully', () => {
    const bm = new BoardMeeting();
    const update = bm.generateInvestorUpdate('April 2026');
    expect(update).toContain('April 2026');
    expect(update).toContain('No decisions recorded');
  });
});
