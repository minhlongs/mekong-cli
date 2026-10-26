export interface AllModules {
  activeCount: number;
}
export interface AgencyDNA {
  version: string;
}
export interface ClientMagnetStats {
  totalLeads: number;
}
export interface RevenueEngineStats {
  mrr: number;
}
export interface ContentFactoryStats {
  published: number;
}
export interface FranchiseStats {
  nodes: number;
}
export interface VCMetrics {
  readinessScore: number;
}
export interface DataMoatStats {
  records: number;
}

export const antigravityAPI = {
  async getAllModules(): Promise<AllModules> {
    return { activeCount: 25 };
  },
  async getAgencyDNA(): Promise<AgencyDNA> {
    return { version: '6.0.0' };
  },
  async getClientMagnetStats(): Promise<ClientMagnetStats> {
    return { totalLeads: 42 };
  },
  async getRevenueEngineStats(): Promise<RevenueEngineStats> {
    return { mrr: 10375 };
  },
  async getContentFactoryStats(): Promise<ContentFactoryStats> {
    return { published: 128 };
  },
  async getFranchiseStats(): Promise<FranchiseStats> {
    return { nodes: 4 };
  },
  async getVCMetrics(): Promise<VCMetrics> {
    return { readinessScore: 100 };
  },
  async getDataMoatStats(): Promise<DataMoatStats> {
    return { records: 1500 };
  },
  async resetDemoData(): Promise<void> {
    return;
  },
};
