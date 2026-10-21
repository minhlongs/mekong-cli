/**
 * types/api.ts — TypeScript types for Mekong Platform Cyber-Bento Horizon
 */

export interface ScreenMetadata {
  href: string;
  title: string;
  group: 'Core' | 'Operations' | 'Compliance' | 'Recipes' | 'Integrations' | 'Developer' | 'Executive' | string;
  stitch_id: string;
}

export interface PlatformStatus {
  status: 'demo' | 'healthy' | 'degraded' | 'offline' | string;
  uptime_seconds: number;
  version: string;
  mode: 'synthetic_demo' | string;
  screens_count: number;
  active_agents: number;
  swarm_sync: string;
  timestamp: number;
  demo_only: true;
}

export interface VietQRSimulateResponse {
  success: boolean;
  simulated: true;
  demo_only: true;
  order_id: string;
  amount_vnd: number;
  simulated_mcu: number;
  bank_code: string;
  verified: false;
  notice: string;
  timestamp: number;
  mode: 'demo_simulation';
}

export interface TT78VerifyResponse {
  valid: boolean;
  demo_only: true;
  invoice_id: string;
  seller_tax_id: string;
  buyer_tax_id: string;
  amount_vnd: number;
  vat_amount: number;
  total_with_vat: number;
  vat_rate: number;
  hash_payload: string;
  canonical_string: string;
  digital_stamp: string;
  standard: 'TT78/2021/TT-BTC & ND123/2020/ND-CP';
  mode: 'synthetic_demo';
  timestamp: number;
}

export interface CSuiteQuorumResponse {
  demo_only: true;
  quorum_reached: boolean;
  required_approvals: number;
  total_votes: number;
  signoff_hash: string;
  signers: Array<{
    role: string;
    name: string;
    status: 'CONFIRMED' | 'PENDING' | 'REJECTED';
    timestamp: number;
  }>;
  resolution: string;
  timestamp: number;
  mode: 'synthetic_demo';
}

export interface MerkleAuditResponse {
  demo_only: true;
  merkle_root: string;
  leaf_count: number;
  leaves: string[];
  depth: number;
  verified: boolean;
  standard: 'NIST-FIPS-180-4' | string;
  timestamp: number;
  mode: 'synthetic_demo';
}
