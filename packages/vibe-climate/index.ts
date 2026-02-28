/**
 * @agencyos/vibe-climate — Climate Tech Facade SDK
 *
 * Carbon tracking, ESG scorecard, green certificate management, emissions reporting.
 *
 * Usage:
 *   import { createCarbonTracker, createESGScorecard, createGreenCertificateManager } from '@agencyos/vibe-climate';
 */

// ─── Types ──────────────────────────────────────────────────────

export type EmissionScope = 'scope1' | 'scope2' | 'scope3';
export type EmissionUnit = 'kg' | 'tonnes' | 'lbs';
export type ESGCategory = 'environmental' | 'social' | 'governance';
export type CertificateStatus = 'pending' | 'active' | 'retired' | 'expired' | 'cancelled';
export type CertificateType = 'REC' | 'carbon_credit' | 'gold_standard' | 'verified_carbon_unit';

export interface EmissionSource {
  id: string;
  name: string;
  scope: EmissionScope;
  category: string;
  amountKg: number;
  activityData: number;
  activityUnit: string;
  emissionFactor: number;
  recordedAt: string;
}

export interface CarbonFootprint {
  scope1Kg: number;
  scope2Kg: number;
  scope3Kg: number;
  totalKg: number;
  totalTonnes: number;
  periodStart: string;
  periodEnd: string;
  sources: EmissionSource[];
}

export interface ESGScore {
  category: ESGCategory;
  score: number;
  maxScore: number;
  percentile: number;
  benchmarkScore: number;
  indicators: ESGIndicator[];
  assessedAt: string;
}

export interface ESGIndicator {
  id: string;
  name: string;
  category: ESGCategory;
  value: number;
  unit: string;
  target: number;
  weight: number;
  score: number;
}

export interface GreenCertificate {
  id: string;
  type: CertificateType;
  status: CertificateStatus;
  quantityMWh?: number;
  quantityCO2Tonnes?: number;
  issuer: string;
  projectName: string;
  vintageYear: number;
  issuedAt: string;
  expiresAt?: string;
  retiredAt?: string;
  serialNumber: string;
}

export interface CarbonOffsetPlan {
  totalEmissionsKg: number;
  offsetRequiredTonnes: number;
  recommendedCertificates: CertificateType[];
  estimatedCostUSD: number;
  achievableNetzero: boolean;
}

// ─── Carbon Tracker ─────────────────────────────────────────────

export function createCarbonTracker() {
  const sources: EmissionSource[] = [];

  return {
    /** Ghi nhận nguồn phát thải mới */
    addEmissionSource(source: EmissionSource): EmissionSource[] {
      sources.push({ ...source });
      return [...sources];
    },

    /** Xoá nguồn phát thải theo id */
    removeEmissionSource(id: string): EmissionSource[] {
      const idx = sources.findIndex(s => s.id === id);
      if (idx !== -1) sources.splice(idx, 1);
      return [...sources];
    },

    /** Tính carbon footprint cho khoảng thời gian */
    calculateFootprint(periodStart: string, periodEnd: string): CarbonFootprint {
      const inRange = sources.filter(s => s.recordedAt >= periodStart && s.recordedAt <= periodEnd);
      const scope1Kg = inRange.filter(s => s.scope === 'scope1').reduce((sum, s) => sum + s.amountKg, 0);
      const scope2Kg = inRange.filter(s => s.scope === 'scope2').reduce((sum, s) => sum + s.amountKg, 0);
      const scope3Kg = inRange.filter(s => s.scope === 'scope3').reduce((sum, s) => sum + s.amountKg, 0);
      const totalKg = scope1Kg + scope2Kg + scope3Kg;
      return {
        scope1Kg, scope2Kg, scope3Kg,
        totalKg,
        totalTonnes: Math.round((totalKg / 1000) * 100) / 100,
        periodStart, periodEnd,
        sources: inRange,
      };
    },

    /** Tạo kế hoạch bù đắp carbon */
    createOffsetPlan(footprint: CarbonFootprint, costPerTonneCO2: number = 15): CarbonOffsetPlan {
      const offsetRequiredTonnes = footprint.totalTonnes;
      const estimatedCostUSD = Math.round(offsetRequiredTonnes * costPerTonneCO2 * 100) / 100;
      const recommended: CertificateType[] = [];
      if (footprint.scope2Kg > 0) recommended.push('REC');
      if (footprint.scope1Kg + footprint.scope3Kg > 0) recommended.push('verified_carbon_unit');
      return {
        totalEmissionsKg: footprint.totalKg,
        offsetRequiredTonnes,
        recommendedCertificates: recommended,
        estimatedCostUSD,
        achievableNetzero: estimatedCostUSD > 0,
      };
    },

    /** Sinh báo cáo phát thải theo scope */
    generateReport(periodStart: string, periodEnd: string): Record<EmissionScope, { totalKg: number; sources: EmissionSource[] }> {
      const footprint = this.calculateFootprint(periodStart, periodEnd);
      return {
        scope1: { totalKg: footprint.scope1Kg, sources: footprint.sources.filter(s => s.scope === 'scope1') },
        scope2: { totalKg: footprint.scope2Kg, sources: footprint.sources.filter(s => s.scope === 'scope2') },
        scope3: { totalKg: footprint.scope3Kg, sources: footprint.sources.filter(s => s.scope === 'scope3') },
      };
    },

    getSources: () => [...sources],
  };
}

// ─── ESG Scorecard ──────────────────────────────────────────────

export function createESGScorecard() {
  return {
    /** Tính điểm ESG từ danh sách indicators */
    calculateScore(indicators: ESGIndicator[], category: ESGCategory, benchmarkScore: number = 60): ESGScore {
      const catIndicators = indicators.filter(i => i.category === category);
      const totalWeight = catIndicators.reduce((sum, i) => sum + i.weight, 0);
      const weightedScore = totalWeight === 0 ? 0 :
        catIndicators.reduce((sum, i) => sum + (i.score * i.weight), 0) / totalWeight;
      const score = Math.round(weightedScore * 100) / 100;
      const maxScore = 100;
      const percentile = Math.round((score / maxScore) * 100);
      return { category, score, maxScore, percentile, benchmarkScore, indicators: catIndicators, assessedAt: new Date().toISOString() };
    },

    /** So sánh điểm với benchmark ngành */
    compareToBenchmark(score: ESGScore): { delta: number; aboveBenchmark: boolean; rating: string } {
      const delta = Math.round((score.score - score.benchmarkScore) * 100) / 100;
      const rating = score.score >= 80 ? 'Leader' : score.score >= 60 ? 'Average' : score.score >= 40 ? 'Laggard' : 'Critical';
      return { delta, aboveBenchmark: delta >= 0, rating };
    },

    /** Tổng hợp điểm ESG tổng thể từ 3 category */
    getCompositeScore(scores: ESGScore[]): { composite: number; breakdown: Record<ESGCategory, number> } {
      const weights: Record<ESGCategory, number> = { environmental: 0.4, social: 0.35, governance: 0.25 };
      const breakdown = {} as Record<ESGCategory, number>;
      let composite = 0;
      for (const s of scores) {
        breakdown[s.category] = s.score;
        composite += s.score * weights[s.category];
      }
      return { composite: Math.round(composite * 100) / 100, breakdown };
    },

    /** Tìm indicators cần cải thiện nhất */
    getImprovementPriorities(indicators: ESGIndicator[], topN: number = 3): ESGIndicator[] {
      return [...indicators]
        .filter(i => i.score < i.target)
        .sort((a, b) => (b.weight * (b.target - b.score)) - (a.weight * (a.target - a.score)))
        .slice(0, topN);
    },
  };
}

// ─── Green Certificate Manager ──────────────────────────────────

export function createGreenCertificateManager() {
  const certificates: GreenCertificate[] = [];

  return {
    /** Thêm chứng chỉ xanh mới */
    addCertificate(cert: GreenCertificate): GreenCertificate[] {
      certificates.push({ ...cert });
      return [...certificates];
    },

    /** Thu hồi (retire) chứng chỉ để ghi nhận offset */
    retireCertificate(id: string): { ok: boolean; certificate?: GreenCertificate; reason?: string } {
      const cert = certificates.find(c => c.id === id);
      if (!cert) return { ok: false, reason: 'Certificate not found' };
      if (cert.status !== 'active') return { ok: false, reason: `Cannot retire certificate with status: ${cert.status}` };
      cert.status = 'retired';
      cert.retiredAt = new Date().toISOString();
      return { ok: true, certificate: { ...cert } };
    },

    /** Tính tổng MWh từ RECs đang active */
    getTotalRenewableEnergyMWh(): number {
      return certificates
        .filter(c => c.type === 'REC' && c.status === 'active')
        .reduce((sum, c) => sum + (c.quantityMWh ?? 0), 0);
    },

    /** Tính tổng CO2 đã offset qua carbon credits đã retired */
    getTotalOffsetTonnes(): number {
      return certificates
        .filter(c => c.type !== 'REC' && c.status === 'retired')
        .reduce((sum, c) => sum + (c.quantityCO2Tonnes ?? 0), 0);
    },

    /** Lọc chứng chỉ sắp hết hạn */
    getExpiringCertificates(withinDays: number = 90): GreenCertificate[] {
      const threshold = new Date(Date.now() + withinDays * 86400000).toISOString();
      return certificates.filter(c => c.status === 'active' && c.expiresAt && c.expiresAt <= threshold);
    },

    getCertificates: () => [...certificates],
  };
}
