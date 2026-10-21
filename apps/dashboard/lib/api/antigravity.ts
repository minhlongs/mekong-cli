/**
 * Synthetic Demo Antigravity API Client (Pilot Demo Only)
 */

export interface AgencyDNA {
  niche: string
  positioning: string
  synthetic: boolean
}

export interface ClientMagnetStats {
  total_leads: number
  qualified_leads: number
  synthetic: boolean
}

export interface RevenueEngineStats {
  mrr: number
  arr: number
  synthetic: boolean
}

export interface ContentFactoryStats {
  published: number
  queued: number
  synthetic: boolean
}

export interface FranchiseStats {
  active_nodes: number
  synthetic: boolean
}

export interface VCMetrics {
  readiness_score: number
  synthetic: boolean
}

export interface DataMoatStats {
  playbooks_indexed: number
  synthetic: boolean
}

export interface AllModules {
  dna: AgencyDNA
  leads: ClientMagnetStats
  revenue: RevenueEngineStats
  content: ContentFactoryStats
  franchise: FranchiseStats
  vc: VCMetrics
  moat: DataMoatStats
}

const SYNTHETIC_MODULES: AllModules = {
  dna: { niche: 'B2B AI Automation (Synthetic)', positioning: 'Invited Pilot Demo', synthetic: true },
  leads: { total_leads: 42, qualified_leads: 18, synthetic: true },
  revenue: { mrr: 10375, arr: 124500, synthetic: true },
  content: { published: 24, queued: 12, synthetic: true },
  franchise: { active_nodes: 5, synthetic: true },
  vc: { readiness_score: 88, synthetic: true },
  moat: { playbooks_indexed: 39, synthetic: true },
}

export const antigravityAPI = {
  async getAllModules(): Promise<AllModules> {
    return SYNTHETIC_MODULES
  },
  async getAgencyDNA(): Promise<AgencyDNA> {
    return SYNTHETIC_MODULES.dna
  },
  async getClientMagnetStats(): Promise<ClientMagnetStats> {
    return SYNTHETIC_MODULES.leads
  },
  async getRevenueEngineStats(): Promise<RevenueEngineStats> {
    return SYNTHETIC_MODULES.revenue
  },
  async getContentFactoryStats(): Promise<ContentFactoryStats> {
    return SYNTHETIC_MODULES.content
  },
  async getFranchiseStats(): Promise<FranchiseStats> {
    return SYNTHETIC_MODULES.franchise
  },
  async getVCMetrics(): Promise<VCMetrics> {
    return SYNTHETIC_MODULES.vc
  },
  async getDataMoatStats(): Promise<DataMoatStats> {
    return SYNTHETIC_MODULES.moat
  },
  async resetDemoData(): Promise<void> {
    return
  },
}
