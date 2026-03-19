export interface CommissionSummary {
  totalReferrals: number;
  totalRevenue: number;
  commissionEarned: number;
  commissionRate: number;
}

export interface AffiliateStats {
  affiliateId: string;
  referrals: number;
  revenue: number;
  commission: number;
}

interface ReferralRecord {
  affiliateId: string;
  purchaseAmount: number;
  timestamp: Date;
}

export class AffiliateProgram {
  private readonly defaultCommissionRate = 0.20; // 20%
  private referrals: ReferralRecord[] = [];
  private commissionRates: Map<string, number> = new Map();

  createReferralLink(affiliateId: string, productId: string): string {
    const encoded = Buffer.from(`${affiliateId}:${productId}`).toString("base64url");
    return `https://openclaw.io/ref/${encoded}?aff=${encodeURIComponent(affiliateId)}&product=${encodeURIComponent(productId)}`;
  }

  trackReferral(affiliateId: string, purchaseAmount: number): void {
    this.referrals.push({ affiliateId, purchaseAmount, timestamp: new Date() });
  }

  getCommission(affiliateId: string): CommissionSummary {
    const records = this.referrals.filter((r) => r.affiliateId === affiliateId);
    const rate = this.commissionRates.get(affiliateId) ?? this.defaultCommissionRate;
    const totalRevenue = records.reduce((s, r) => s + r.purchaseAmount, 0);
    const commissionEarned = Math.round(totalRevenue * rate * 100) / 100;

    return {
      totalReferrals: records.length,
      totalRevenue: Math.round(totalRevenue * 100) / 100,
      commissionEarned,
      commissionRate: rate,
    };
  }

  setCommissionRate(affiliateId: string, rate: number): void {
    if (rate < 0 || rate > 1) throw new Error("Rate must be between 0 and 1");
    this.commissionRates.set(affiliateId, rate);
  }

  listTopAffiliates(n: number): AffiliateStats[] {
    const byAffiliate = new Map<string, ReferralRecord[]>();

    for (const r of this.referrals) {
      const list = byAffiliate.get(r.affiliateId) ?? [];
      list.push(r);
      byAffiliate.set(r.affiliateId, list);
    }

    const stats: AffiliateStats[] = Array.from(byAffiliate.entries()).map(
      ([affiliateId, records]) => {
        const rate = this.commissionRates.get(affiliateId) ?? this.defaultCommissionRate;
        const revenue = records.reduce((s, r) => s + r.purchaseAmount, 0);
        return {
          affiliateId,
          referrals: records.length,
          revenue: Math.round(revenue * 100) / 100,
          commission: Math.round(revenue * rate * 100) / 100,
        };
      }
    );

    return stats.sort((a, b) => b.revenue - a.revenue).slice(0, n);
  }
}
