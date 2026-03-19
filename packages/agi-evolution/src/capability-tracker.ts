export type CapabilityType = 'command' | 'skill' | 'adapter';

export interface Capability {
  name: string;
  type: CapabilityType;
  path: string;
  usageCount: number;
  successCount: number;
  lastUsed: Date | null;
  registeredAt: Date;
}

export interface CapabilityStats {
  total: number;
  byType: Record<CapabilityType, number>;
  successRate: number;
  mostUsed: string[];
}

export class CapabilityRegistry {
  private readonly store = new Map<string, Capability>();

  register(name: string, type: CapabilityType, path: string): void {
    if (this.store.has(name)) return;
    this.store.set(name, {
      name,
      type,
      path,
      usageCount: 0,
      successCount: 0,
      lastUsed: null,
      registeredAt: new Date(),
    });
  }

  track(name: string, success: boolean): void {
    const cap = this.store.get(name);
    if (!cap) throw new Error(`Capability not registered: ${name}`);
    cap.usageCount += 1;
    if (success) cap.successCount += 1;
    cap.lastUsed = new Date();
  }

  getStats(): CapabilityStats {
    const all = [...this.store.values()];
    const byType: Record<CapabilityType, number> = { command: 0, skill: 0, adapter: 0 };
    let totalUsage = 0;
    let totalSuccess = 0;

    for (const cap of all) {
      byType[cap.type] += 1;
      totalUsage += cap.usageCount;
      totalSuccess += cap.successCount;
    }

    return {
      total: all.length,
      byType,
      successRate: totalUsage === 0 ? 0 : totalSuccess / totalUsage,
      mostUsed: this.getPopular(5),
    };
  }

  getPopular(n: number): string[] {
    return [...this.store.values()]
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, n)
      .map((c) => c.name);
  }

  getDeprecated(threshold: number): string[] {
    return [...this.store.values()]
      .filter((c) => c.usageCount < threshold)
      .map((c) => c.name);
  }

  autoDeprecate(minUsage: number, daysSinceLastUse: number): string[] {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - daysSinceLastUse);

    const toDeprecate: string[] = [];
    for (const cap of this.store.values()) {
      const isUnderused = cap.usageCount < minUsage;
      const isStale = cap.lastUsed === null || cap.lastUsed < cutoff;
      if (isUnderused && isStale) toDeprecate.push(cap.name);
    }
    return toDeprecate;
  }

  get(name: string): Capability | undefined {
    return this.store.get(name);
  }

  list(): Capability[] {
    return [...this.store.values()];
  }
}
