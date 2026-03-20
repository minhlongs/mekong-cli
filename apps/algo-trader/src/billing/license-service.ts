/**
 * License Service
 * ROIaaS Phase 2 - License CRUD and key generation
 */

import {
  License,
  LicenseTier,
  LicenseStatus,
  CreateLicenseInput,
  LicenseFilters,
  LicenseListResponse,
} from '../types/license';

const LICENSE_PREFIX = 'raas';
const TIER_PREFIXES: Record<LicenseTier, string> = {
  [LicenseTier.FREE]: 'free',
  [LicenseTier.PRO]: 'rpp',
  [LicenseTier.ENTERPRISE]: 'rep',
};

export class LicenseService {
  private static instance: LicenseService;
  private licenses: Map<string, License> = new Map();

  private constructor() {}

  static getInstance(): LicenseService {
    if (!LicenseService.instance) {
      LicenseService.instance = new LicenseService();
    }
    return LicenseService.instance;
  }

  generateLicenseKey(tier: LicenseTier): string {
    const tierPrefix = TIER_PREFIXES[tier];
    const segment1 = this.generateRandomSegment(8);
    const segment2 = this.generateRandomSegment(8);
    return `${LICENSE_PREFIX}-${tierPrefix}-${segment1}-${segment2}`.toUpperCase();
  }

  private generateRandomSegment(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }

  async createLicense(input: CreateLicenseInput): Promise<License> {
    const id = `lic_${this.generateId()}`;
    const key = this.generateLicenseKey(input.tier);
    const now = new Date().toISOString();

    const license: License = {
      id,
      name: input.name,
      key,
      tier: input.tier,
      status: LicenseStatus.ACTIVE,
      createdAt: now,
      updatedAt: now,
      usageCount: 0,
      maxUsage: this.getDefaultMaxUsage(input.tier),
      tenantId: input.tenantId,
      domain: input.domain,
      expiresAt: input.expiresAt,
    };

    this.licenses.set(id, license);
    return license;
  }

  private getDefaultMaxUsage(tier: LicenseTier): number {
    switch (tier) {
      case LicenseTier.FREE:
        return 100;
      case LicenseTier.PRO:
        return 10000;
      case LicenseTier.ENTERPRISE:
        return 100000;
    }
  }

  getLicense(id: string): License | undefined {
    return this.licenses.get(id);
  }

  getLicenseByKey(key: string): License | undefined {
    for (const license of this.licenses.values()) {
      if (license.key === key) {
        return license;
      }
    }
    return undefined;
  }

  getLicenseBySubscription(subscriptionId: string): License | undefined {
    for (const license of this.licenses.values()) {
      if (license.subscriptionId === subscriptionId) {
        return license;
      }
    }
    return undefined;
  }

  async listLicenses(filters: LicenseFilters = {}): Promise<LicenseListResponse> {
    let result = Array.from(this.licenses.values());

    if (filters.status && filters.status !== 'all') {
      result = result.filter((l) => l.status === filters.status);
    }

    if (filters.tier && filters.tier !== 'all') {
      result = result.filter((l) => l.tier === filters.tier);
    }

    const total = result.length;
    const skip = filters.skip || 0;
    const take = filters.take || 10;

    result = result.slice(skip, skip + take);

    return {
      licenses: result,
      total,
      hasMore: skip + take < total,
    };
  }

  async revokeLicense(id: string): Promise<License | undefined> {
    const license = this.licenses.get(id);
    if (!license) {
      return undefined;
    }

    license.status = LicenseStatus.REVOKED;
    license.updatedAt = new Date().toISOString();
    this.licenses.set(id, license);
    return license;
  }

  async deleteLicense(id: string): Promise<boolean> {
    return this.licenses.delete(id);
  }

  async getAnalytics() {
    const allLicenses = Array.from(this.licenses.values());

    const byTier = {
      [LicenseTier.FREE]: allLicenses.filter((l) => l.tier === LicenseTier.FREE).length,
      [LicenseTier.PRO]: allLicenses.filter((l) => l.tier === LicenseTier.PRO).length,
      [LicenseTier.ENTERPRISE]: allLicenses.filter((l) => l.tier === LicenseTier.ENTERPRISE).length,
    };

    const byStatus = {
      [LicenseStatus.ACTIVE]: allLicenses.filter((l) => l.status === LicenseStatus.ACTIVE).length,
      [LicenseStatus.EXPIRED]: allLicenses.filter((l) => l.status === LicenseStatus.EXPIRED).length,
      [LicenseStatus.REVOKED]: allLicenses.filter((l) => l.status === LicenseStatus.REVOKED).length,
    };

    const recentActivity = allLicenses
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, 10)
      .map((l) => ({
        licenseId: l.id,
        licenseName: l.name,
        event: 'created',
        timestamp: l.createdAt,
      }));

    return {
      totalLicenses: allLicenses.length,
      byTier,
      byStatus,
      totalRevenue: 0,
      mrr: 0,
      avgLicenseValue: 0,
      recentActivity,
    };
  }

  private generateId(): string {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  }
}
