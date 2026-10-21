/**
 * services/api.ts — Dual-mode API client for Mekong Platform Cyber-Bento Horizon.
 * Returns synthetic demo data only. Hashes are demonstrations and never prove
 * invoice authenticity, executive approval, or payment settlement.
 */

import {
  ScreenMetadata,
  PlatformStatus,
  VietQRSimulateResponse,
  TT78VerifyResponse,
  CSuiteQuorumResponse,
  MerkleAuditResponse
} from '../types/api';

export const SCREENS_CATALOG: ScreenMetadata[] = [
  { href: "index.html", title: "01 Landing — Hero & Open-Core Overview", group: "Core", stitch_id: "87ad4560e1ca44a0a45d2e09cb436d3a" },
  { href: "pricing.html", title: "02 Pricing — Transparent Pricing Matrix", group: "Core", stitch_id: "5bb5af1c510642249d80437147ab92c8" },
  { href: "cockpit.html", title: "03 Cockpit — Desktop Agent Swarm Topology", group: "Operations", stitch_id: "f496e91c170a4ade8dc8284d0ec5b1c0" },
  { href: "billing.html", title: "04 Billing — Cloud Control Plane & MCU Meter", group: "Operations", stitch_id: "be5b9d1d081148e8b661653bc542199c" },
  { href: "audit.html", title: "05 Audit — Immutable SHA-256 Compliance Ledger", group: "Compliance", stitch_id: "d47c7bedd4ab4081b22b5dd7355829b1" },
  { href: "marketplace.html", title: "06 Marketplace — Strategy Recipe Creator Hub", group: "Recipes", stitch_id: "e4066339f9fe4c76a74dd7f4cb4d2237" },
  { href: "settings.html", title: "07 Settings — Enterprise Multi-Tenant & Vault", group: "Operations", stitch_id: "f3173dda4bca469e8461afaad763f0df" },
  { href: "styleguide.html", title: "08 Styleguide — Component Style Guide Catalog", group: "Design", stitch_id: "dabed64cfa4a45b2b013780d15358ebc" },
  { href: "docs.html", title: "09 Docs — Developer CLI & SDK Reference", group: "Core", stitch_id: "db0ead813f6344fba5505734fa02e65e" },
  { href: "playground.html", title: "10 Playground — WebAssembly CLI Sandbox", group: "Developer", stitch_id: "26c7a8a9498340958f5f8cf11d1305c2" },
  { href: "invoice-verifier.html", title: "11 Invoice Verifier — TT78 / NĐ 123 Inspector", group: "Compliance", stitch_id: "af7fe94874ad4dcb85ca58bd3c07407c" },
  { href: "swarm-monitor.html", title: "12 Swarm Monitor — Distributed WebSocket Stream", group: "Operations", stitch_id: "dff59f17ccf74a35a4966815f2eb90f7" },
  { href: "status.html", title: "13 Status — Global Microservice SLA Dashboard", group: "Operations", stitch_id: "88b2469fde664b4bbc2cdb981392570d" },
  { href: "recipe-builder.html", title: "14 Recipe Builder — Visual Workflow Studio", group: "Recipes", stitch_id: "467f39c14d504611bf62eadbb25030c6" },
  { href: "zalo-oa-console.html", title: "15 Zalo OA — Engagement & Broadcast Console", group: "Integrations", stitch_id: "24a56db3ecb44983bba4e2379c26a63a" },
  { href: "agent-debugger.html", title: "16 Agent Debugger — Live DAG & Execution Visualizer", group: "Developer", stitch_id: "a199abedbe004fc0adaf30ff6d5fcd5a" },
  { href: "vietqr-webhook-tester.html", title: "17 VietQR Tester — Webhook Receiver Simulator", group: "Integrations", stitch_id: "7e9686a21d794569bf319f3ed141aa30" },
  { href: "compliance-vault.html", title: "18 Compliance Vault — SOC-2 & Merkle Proof Browser", group: "Compliance", stitch_id: "2058b0b534704dc493c5204814afcc4e" },
  { href: "c-suite-boardroom.html", title: "19 C-Suite Boardroom — Executive War Room & OKR Telemetry", group: "Executive", stitch_id: "7a7122ec87844012b62aa1f95ebd7916" },
  { href: "fintech-treasury.html", title: "20 Fintech Treasury — Multi-Bank VietQR & Cashflow Runway", group: "Fintech", stitch_id: "5bbdb79f45fd4d78bfa0eae01a768486" },
  { href: "zero-to-ipo-launchpad.html", title: "21 Zero-to-IPO Launchpad — Cap Table & SBV Compliance", group: "Executive", stitch_id: "e856db6b532e4facbd997edb6bada3c9" }
];

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

async function sha256Hex(text: string): Promise<string> {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
    const enc = new TextEncoder();
    const buf = await window.crypto.subtle.digest('SHA-256', enc.encode(text));
    return Array.from(new Uint8Array(buf))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }
  return 'sha256_mock_' + Math.random().toString(16).substring(2, 10);
}

export async function fetchScreens(): Promise<ScreenMetadata[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/screens`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      const data = await res.json();
      return data.screens || SCREENS_CATALOG;
    }
  } catch {
    // fallback
  }
  return SCREENS_CATALOG;
}

export async function fetchPlatformStatus(): Promise<PlatformStatus> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/status`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // fallback
  }
  return {
    status: 'demo',
    uptime_seconds: 0,
    version: '6.0.0-pro',
    mode: 'synthetic_demo',
    screens_count: 21,
    active_agents: 0,
    swarm_sync: 'NOT_CONNECTED',
    timestamp: Date.now() / 1000,
    demo_only: true
  };
}

export async function simulateVietQR(
  amount: number = 250000,
  orderId?: string,
  bankCode: string = 'VCB'
): Promise<VietQRSimulateResponse> {
  const payload = { amount, order_id: orderId, bank_code: bankCode };
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/vietqr/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(2000)
    });
    if (res.ok) {
      const data = await res.json();
      if (data?.simulated === true && data?.demo_only === true && data?.verified === false) {
        return { ...data, mode: 'demo_simulation' };
      }
      return {
        success: false,
        simulated: true,
        demo_only: true,
        order_id: orderId || `DEMO-${Date.now().toString().slice(-6)}`,
        amount_vnd: amount,
        simulated_mcu: Math.floor(amount / 1000),
        bank_code: bankCode,
        verified: false,
        notice: 'No payment was processed because the endpoint did not return a demo-only response.',
        timestamp: Date.now() / 1000,
        mode: 'demo_simulation'
      };
    }
  } catch {
    // Fallback using client-side crypto
  }

  const resolvedOrder = orderId || `DEMO-${Date.now().toString().slice(-6)}`;
  return {
    success: true,
    simulated: true,
    demo_only: true,
    order_id: resolvedOrder,
    amount_vnd: amount,
    simulated_mcu: Math.floor(amount / 1000),
    bank_code: bankCode,
    verified: false,
    notice: 'Demo only. No payment, webhook verification, or MCU credit was performed.',
    timestamp: Date.now() / 1000,
    mode: 'demo_simulation'
  };
}

export async function verifyTT78(
  invoiceId: string = 'INV-2026-009842',
  sellerTaxId: string = '0312345678',
  buyerTaxId: string = '0109876543',
  amountVnd: number = 15400000,
  vatRate: number = 10
): Promise<TT78VerifyResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/tt78/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ invoice_id: invoiceId, seller_tax_id: sellerTaxId, buyer_tax_id: buyerTaxId, amount_vnd: amountVnd, vat_rate: vatRate }),
      signal: AbortSignal.timeout(2000)
    });
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }

  const vat = Math.round(amountVnd * (vatRate / 100));
  const total = amountVnd + vat;
  const canonical = `${invoiceId}|${sellerTaxId}|${buyerTaxId}|${amountVnd}|${vatRate}|${total}`;
  const stamp = await sha256Hex(canonical);

  return {
    valid: false,
    demo_only: true,
    invoice_id: invoiceId,
    seller_tax_id: sellerTaxId,
    buyer_tax_id: buyerTaxId,
    amount_vnd: amountVnd,
    vat_amount: vat,
    total_with_vat: total,
    vat_rate: vatRate,
    hash_payload: stamp,
    canonical_string: canonical,
    digital_stamp: `DEMO-HASH-ONLY-${stamp.substring(0, 16).toUpperCase()}`,
    standard: 'TT78/2021/TT-BTC & ND123/2020/ND-CP',
    mode: 'synthetic_demo',
    timestamp: Date.now() / 1000
  };
}

export async function fetchCSuiteQuorum(): Promise<CSuiteQuorumResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/c-suite/quorum`, { signal: AbortSignal.timeout(1500) });
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }

  const signoff = await sha256Hex('demo_no_executive_approvals');
  return {
    demo_only: true,
    quorum_reached: false,
    required_approvals: 5,
    total_votes: 0,
    signoff_hash: signoff,
    signers: [],
    resolution: 'Demo only. No executive approvals were recorded.',
    timestamp: Date.now() / 1000,
    mode: 'synthetic_demo'
  };
}

export async function computeMerkleAudit(records?: string[]): Promise<MerkleAuditResponse> {
  const recs = records && records.length > 0 ? records : [
    "demo_record:session_root_sample",
    "demo_record:invoice_hash_sample",
    "demo_record:payment_not_processed"
  ];

  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/audit/merkle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ records: recs }),
      signal: AbortSignal.timeout(2000)
    });
    if (res.ok) return await res.json();
  } catch {
    // fallback
  }

  const leaves = await Promise.all(recs.map(r => sha256Hex(r)));
  const root = await sha256Hex(leaves.join(''));
  return {
    merkle_root: root,
    demo_only: true,
    leaf_count: leaves.length,
    leaves,
    depth: 3,
    verified: false,
    standard: 'NIST-FIPS-180-4',
    timestamp: Date.now() / 1000,
    mode: 'synthetic_demo'
  };
}
