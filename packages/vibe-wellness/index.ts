/**
 * @agencyos/vibe-wellness — Wellness & TCM Operations SDK
 *
 * Reusable across wellness/TCM/health projects (anima119).
 * Product formulation, ingredient tracking, compliance, subscription boxes.
 *
 * Usage:
 *   import { createFormulationEngine, HerbProperty } from '@agencyos/vibe-wellness';
 *   const engine = createFormulationEngine();
 *   const formula = engine.validateFormula([...herbs]);
 */

// ─── Types ──────────────────────────────────────────────────────

export type HerbNature = 'hot' | 'warm' | 'neutral' | 'cool' | 'cold';
export type HerbFlavor = 'sour' | 'bitter' | 'sweet' | 'spicy' | 'salty';
export type HerbRole = 'quan' | 'than' | 'ta' | 'su'; // Quân-Thần-Tá-Sứ

export interface HerbProperty {
  id: string;
  name: string;
  vietnameseName: string;
  nature: HerbNature;
  flavors: HerbFlavor[];
  role: HerbRole;
  dosageGrams: number;
  contraindications: string[];
}

export interface Formula {
  id: string;
  name: string;
  herbs: HerbProperty[];
  totalWeight: number;
  isBalanced: boolean;
  warnings: string[];
}

export interface WellnessProduct {
  id: string;
  name: string;
  type: 'fermented' | 'dried-herb' | 'tincture' | 'tea-blend' | 'supplement';
  formula?: Formula;
  shelfLifeDays: number;
  storageTemp: string;
  certifications: string[];
}

export interface SubscriptionBox {
  id: string;
  tier: 'basic' | 'premium' | 'custom';
  products: WellnessProduct[];
  deliveryFrequency: 'weekly' | 'biweekly' | 'monthly';
  price: number;
}

// ─── Formulation Engine ─────────────────────────────────────────

export function createFormulationEngine() {
  return {
    validateFormula(herbs: HerbProperty[]): { isBalanced: boolean; warnings: string[] } {
      const warnings: string[] = [];

      // Check Quân-Thần-Tá-Sứ balance
      const hasQuan = herbs.some((h) => h.role === 'quan');
      const hasThan = herbs.some((h) => h.role === 'than');
      if (!hasQuan) warnings.push('Thiếu vị thuốc Quân (chủ trị)');
      if (!hasThan) warnings.push('Thiếu vị thuốc Thần (hỗ trợ)');

      // Check nature balance
      const hotCount = herbs.filter((h) => ['hot', 'warm'].includes(h.nature)).length;
      const coldCount = herbs.filter((h) => ['cold', 'cool'].includes(h.nature)).length;
      if (hotCount > 0 && coldCount === 0) warnings.push('Công thức thiên nhiệt, cần thêm vị mát');
      if (coldCount > 0 && hotCount === 0) warnings.push('Công thức thiên hàn, cần thêm vị ấm');

      // Check contraindications
      for (const herb of herbs) {
        for (const other of herbs) {
          if (herb.id !== other.id && herb.contraindications.includes(other.name)) {
            warnings.push(`${herb.name} kỵ dùng chung với ${other.name}`);
          }
        }
      }

      return { isBalanced: warnings.length === 0, warnings };
    },

    calculateTotalWeight(herbs: HerbProperty[]): number {
      return herbs.reduce((sum, h) => sum + h.dosageGrams, 0);
    },

    checkShelfLife(product: WellnessProduct, productionDate: Date): { isExpired: boolean; daysRemaining: number } {
      const now = new Date();
      const expiryDate = new Date(productionDate);
      expiryDate.setDate(expiryDate.getDate() + product.shelfLifeDays);
      const daysRemaining = Math.ceil((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return { isExpired: daysRemaining <= 0, daysRemaining };
    },
  };
}

// ─── Compliance Tracker ─────────────────────────────────────────

export type CertificationType = 'ATTP' | 'GMP' | 'HACCP' | 'ISO22000' | 'ORGANIC' | 'FDA';

export interface ComplianceStatus {
  certification: CertificationType;
  isValid: boolean;
  expiryDate: string;
  lastAuditDate: string;
}

export function createComplianceTracker() {
  return {
    checkExpiring(statuses: ComplianceStatus[], daysAhead: number): ComplianceStatus[] {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() + daysAhead);
      return statuses.filter((s) => new Date(s.expiryDate) <= cutoff);
    },

    getRequiredCerts(productType: WellnessProduct['type']): CertificationType[] {
      const base: CertificationType[] = ['ATTP'];
      if (productType === 'supplement') return [...base, 'GMP', 'FDA'];
      if (productType === 'fermented') return [...base, 'HACCP'];
      return base;
    },
  };
}
