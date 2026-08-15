import type { Brand, LicenseTier } from './tiers.js';
import { tierMeetsMinimum } from './tiers.js';
import { verifyKey } from './verifier.js';
import { LicenseStore, defaultStore } from './store.js';

export interface AccessResult {
  allowed: boolean;
  tier: LicenseTier;
  reason?: string;
}

export interface ActivateResult {
  success: boolean;
  tier?: LicenseTier;
  error?: string;
}

export interface GateStatus {
  activated: boolean;
  tier: LicenseTier;
  brand: Brand;
  expiresAt?: string | null;
}

export interface LicenseGateOptions {
  brand: Brand;
  featureMap?: Record<string, LicenseTier>;
  store?: LicenseStore;
}

export class LicenseGate {
  private readonly brand: Brand;
  private readonly featureMap: Record<string, LicenseTier>;
  private readonly store: LicenseStore;
  private currentTier: LicenseTier = 'free';
  private activated = false;
  private expiresAt: string | null = null;

  constructor({ brand, featureMap = {}, store }: LicenseGateOptions) {
    this.brand = brand;
    this.featureMap = featureMap;
    this.store = store ?? defaultStore;
    this._loadFromStore();
  }

  private _loadFromStore(): void {
    const stored = this.store.load(this.brand);
    if (!stored) return;
    const result = verifyKey(stored);
    if (result.valid && result.tier) {
      this.currentTier = result.tier;
      this.activated = true;
      this.expiresAt = stored.expiresAt;
    }
  }

  canAccess(command: string, requiredTier?: LicenseTier): AccessResult {
    const needed: LicenseTier = requiredTier ?? this.featureMap[command] ?? 'free';
    const allowed = tierMeetsMinimum(this.currentTier, needed);
    return {
      allowed,
      tier: this.currentTier,
      reason: allowed ? undefined : `requires ${needed} tier, current: ${this.currentTier}`,
    };
  }

  activate(keyStr: string): ActivateResult {
    // Parse stored key — caller must provide a full LicenseKey object string or
    // we load from store using the raw key string to match.
    const stored = this.store.listAll().find((e) => e.key.key === keyStr)?.key ?? null;
    if (!stored) {
      // Try to parse as JSON directly (for programmatic use)
      try {
        const parsed = JSON.parse(keyStr);
        const result = verifyKey(parsed);
        if (!result.valid) return { success: false, error: result.reason };
        this.store.save(this.brand, parsed);
        this.currentTier = result.tier!;
        this.activated = true;
        this.expiresAt = parsed.expiresAt;
        return { success: true, tier: result.tier };
      } catch {
        return { success: false, error: 'key not found in store and not valid JSON' };
      }
    }
    const result = verifyKey(stored);
    if (!result.valid) return { success: false, error: result.reason };
    if (stored.brand !== this.brand) {
      return { success: false, error: `key is for brand ${stored.brand}, not ${this.brand}` };
    }
    this.currentTier = result.tier!;
    this.activated = true;
    this.expiresAt = stored.expiresAt;
    return { success: true, tier: result.tier };
  }

  getCurrentTier(): LicenseTier {
    return this.currentTier;
  }

  getStatus(): GateStatus {
    return {
      activated: this.activated,
      tier: this.currentTier,
      brand: this.brand,
      expiresAt: this.expiresAt,
    };
  }
}
