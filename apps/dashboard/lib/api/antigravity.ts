export interface AllModules {
  agencyDna: Record<string, never>;
  clientMagnet: Record<string, never>;
  revenueEngine: Record<string, never>;
  contentFactory: Record<string, never>;
  franchise: Record<string, never>;
}
export interface AgencyDNA {
  id?: string;
  name?: string;
  industry?: string;
  maturity?: string;
  updatedAt?: string;
}
export interface ClientMagnetStats {
  totalLeads?: number;
  conversionRate?: number;
  pipelineValue?: number;
}
export interface RevenueEngineStats {
  mrr?: number;
  arr?: number;
  growthRate?: number;
}
export interface ContentFactoryStats {
  piecesProduced?: number;
  engagementRate?: number;
}
export interface FranchiseStats {
  locations?: number;
  revenue?: number;
}
export type VCMetrics = Record<string, never>;
export type DataMoatStats = Record<string, never>;

const stub = () => null as never;

export const antigravityAPI = {
  status: 'ok',
  modules: {},
  getAllModules: stub,
  getAgencyDNA: stub,
  getClientMagnetStats: stub,
  getRevenueEngineStats: stub,
  getContentFactoryStats: stub,
  getFranchiseStats: stub,
  getVCMetrics: stub,
  getDataMoatStats: stub,
  resetDemoData: async () => ({ ok: true } as const),
} as const;
