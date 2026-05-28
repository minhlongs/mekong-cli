declare module '@openclaw/agi-evolution/self-improver' {
  export function analyzeCodebase(path?: string): any;
  export function getQualityScore(analysis: any): number;
  export function generateRefactoringProposals(analysis: any): any;
}
declare module '@openclaw/agi-evolution/version-tracker' {
  export function checkVersions(): any;
}
declare module '@openclaw/agi-evolution/benchmark' {
  export class BenchmarkRunner {
    run(): any;
    generateCompetitiveReport(): string;
  }
}
declare module '@openclaw/vc-governance/pitch-generator' {
  export class PitchGenerator {
    generatePitchData(kpis: any): any;
    generateOneLiner(): string;
  }
}
declare module '@openclaw/vc-governance/data-room' {
  export class DataRoom {
    listDocuments(): any[];
  }
}
declare module '@openclaw/vc-governance/iso-compliance' {
  export class ComplianceEngine {
    auditISO27001(): any;
    auditSOC2(): any;
    checkGDPR(): any[];
    generateComplianceReport(): string;
  }
}
declare module '@openclaw/vc-governance/exit-engine' {
  export class ExitEngine {
    calculateValuation(method: string, inputs: any): number;
    recommendStrategy(inputs: any): any;
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
