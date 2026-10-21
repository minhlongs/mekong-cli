declare module '@openclaw/agi-evolution/self-improver' {
  export interface CodebaseAnalysis {
    totalFiles: number;
    totalLines: number;
    filesOver200Loc: string[];
    anyTypeCount: number;
    todoFixmeCount: number;
  }
  export interface RefactoringProposal {
    priority: string;
    file: string;
    issue: string;
    suggestion: string;
  }
  export function analyzeCodebase(path?: string): CodebaseAnalysis;
  export function getQualityScore(analysis: CodebaseAnalysis): number;
  export function generateRefactoringProposals(analysis: CodebaseAnalysis): RefactoringProposal[];
}
declare module '@openclaw/agi-evolution/version-tracker' {
  export interface VersionInfo {
    name: string;
    currentVersion?: string;
    latestVersion?: string;
  }
  export function checkVersions(): VersionInfo[];
}
declare module '@openclaw/agi-evolution/benchmark' {
  export class BenchmarkRunner {
    run(): Record<string, unknown>;
    generateCompetitiveReport(): string;
  }
}
declare module '@openclaw/vc-governance/pitch-generator' {
  export interface PitchKpis {
    name: string;
    stage: string;
    mrr: number;
    users: number;
    market: string;
    founded: number;
  }
  export interface PitchData {
    problem: string;
    solution: string;
    market: { tam: number; sam: number; som: number };
  }
  export class PitchGenerator {
    generatePitchData(kpis: PitchKpis): PitchData;
    generateOneLiner(): string;
  }
}
declare module '@openclaw/vc-governance/data-room' {
  export interface DataRoomDocument {
    category: string;
    name: string;
  }
  export class DataRoom {
    listDocuments(): DataRoomDocument[];
  }
}
declare module '@openclaw/vc-governance/iso-compliance' {
  export interface ComplianceAuditResult {
    score: number;
    maxScore: number;
  }
  export interface GdprCheckResult {
    status: 'pass' | 'fail' | string;
    requirement?: string;
  }
  export class ComplianceEngine {
    auditISO27001(): ComplianceAuditResult;
    auditSOC2(): ComplianceAuditResult;
    checkGDPR(): GdprCheckResult[];
    generateComplianceReport(): string;
  }
}
declare module '@openclaw/vc-governance/exit-engine' {
  export interface ValuationInputs {
    annualRevenue: number;
    growthRate: number;
    ebitdaMargin: number;
    discountRate: number;
  }
  export interface StrategyInputs {
    name: string;
    stage: string;
    mrr: number;
    users: number;
    market: string;
    founded: number;
  }
  export interface ExitStrategy {
    type: string;
    probability: number;
    timeline: string;
  }
  export class ExitEngine {
    calculateValuation(method: string, inputs: ValuationInputs): number;
    recommendStrategy(inputs: StrategyInputs): ExitStrategy;
  }
}

declare module '@openclaw/rd-engine/sources/github-trending' {
  export interface TrendingRepo {
    name: string;
    fullName: string;
    description: string;
    stars: number;
    url: string;
    language: string;
    topics: string[];
  }
  export function fetchTrendingRepos(topic?: string): Promise<TrendingRepo[]>;
}

declare module '@openclaw/rd-engine/sources/npm-registry' {
  export interface NpmPackage {
    name: string;
    description: string;
    version: string;
    weeklyDownloads: number;
    url: string;
  }
  export function searchNpmPackages(query?: string): Promise<NpmPackage[]>;
}

declare module '@openclaw/rd-engine/sources/hackernews' {
  export interface HNStory {
    title: string;
    url: string;
    points: number;
    author: string;
    createdAt: string;
  }
  export function fetchHNStories(query: string): Promise<HNStory[]>;
}

declare module '@openclaw/rd-engine/analyzer' {
  export interface RdItem {
    source: "github" | "npm" | "hackernews";
    name: string;
    description: string;
    url: string;
    score: number;
  }
  export function scoreRelevance(item: Omit<RdItem, "score">): number;
  export function filterHighRelevance(items: RdItem[], threshold?: number): RdItem[];
}

declare module '@openclaw/rd-engine/reporter' {
  import type { RdItem } from '@openclaw/rd-engine/analyzer';
  export function generateWeeklyReport(items: RdItem[]): string;
}
