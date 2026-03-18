export type WiringStatus = {
  source: string;
  target: string;
  connected: boolean;
  lastSync: Date | null;
};

export type WiringReport = {
  integrations: WiringStatus[];
  healthyCount: number;
  totalCount: number;
};

type WiringKey = 'adapter-to-orchestrator' | 'rd-to-agi' | 'marketplace-to-billing';

const registry = new Map<WiringKey, WiringStatus>();

function getOrCreate(key: WiringKey, source: string, target: string): WiringStatus {
  const existing = registry.get(key);
  if (existing) return existing;
  const entry: WiringStatus = { source, target, connected: false, lastSync: null };
  registry.set(key, entry);
  return entry;
}

function markConnected(key: WiringKey): WiringStatus {
  const entry = registry.get(key);
  if (!entry) throw new Error(`Wiring key not found: ${key}`);
  entry.connected = true;
  entry.lastSync = new Date();
  return { ...entry };
}

export function wireAdapterToOrchestrator(): WiringStatus {
  getOrCreate('adapter-to-orchestrator', '@openclaw/cli-adapter', '@openclaw/cli-orchestrator');
  return markConnected('adapter-to-orchestrator');
}

export function wireRdToAgi(): WiringStatus {
  getOrCreate('rd-to-agi', '@openclaw/rd-engine', '@openclaw/agi-evolution');
  return markConnected('rd-to-agi');
}

export function wireMarketplaceToBilling(): WiringStatus {
  getOrCreate('marketplace-to-billing', '@openclaw/raas-marketplace', '@openclaw/billing');
  return markConnected('marketplace-to-billing');
}

export function getWiringReport(): WiringReport {
  const integrations = [...registry.values()].map((v) => ({ ...v }));
  const healthyCount = integrations.filter((i) => i.connected).length;
  return { integrations, healthyCount, totalCount: integrations.length };
}
