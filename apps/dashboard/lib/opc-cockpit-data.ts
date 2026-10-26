export type SupportedCurrency = 'USD' | 'VND' | 'EUR';
export type SupportedLanguage = 'en' | 'vi';

export interface OpcActionPayload {
  attachments: string[];
  budget_amount: string;
  budget_currency: SupportedCurrency;
  capability: string;
  connector: string;
  content: string;
  expires_at: number;
  parameters: {
    amount: string;
    project_title: string;
  };
  principal: string;
  recipient: string;
}

export interface OpcLineItem {
  service: string;
  hours: number;
  rate: number;
  subtotal: number;
  isUnpriced: boolean;
}

export type UsageStage = 'estimated' | 'reserved' | 'actual' | 'unknown';

export interface OpcUsageEvent {
  event_id: string;
  run_id: string;
  stage: UsageStage;
  provider: string;
  model: string;
  tokens: number;
  amount: string | null;
  currency: SupportedCurrency;
  pricing_source: string;
}

export const SERVICE_CATALOG: Record<
  string,
  { labelEn: string; labelVi: string; rates: Record<SupportedCurrency, number | null> }
> = {
  architecture_review: {
    labelEn: 'Architecture Review',
    labelVi: 'Thẩm định Kiến trúc Hệ thống',
    rates: { USD: 150, VND: 3750000, EUR: 140 },
  },
  cloud_migration_plan: {
    labelEn: 'Cloud Migration Plan',
    labelVi: 'Kế hoạch Dịch chuyển Cloud',
    rates: { USD: 180, VND: 4500000, EUR: 168 },
  },
  security_audit: {
    labelEn: 'Security & Cryptography Audit',
    labelVi: 'Kiểm toán Bảo mật & Mật mã',
    rates: { USD: 200, VND: 5000000, EUR: 185 },
  },
  custom_connector_bespoke: {
    labelEn: 'Bespoke External Connector (Unpriced / Unknown)',
    labelVi: 'Connector Tùy chỉnh (Chưa định giá / Unknown Cost)',
    rates: { USD: null, VND: null, EUR: null },
  },
};

export function canonicalizePayload(payload: OpcActionPayload): string {
  const ordered = {
    attachments: [...payload.attachments],
    budget_amount: payload.budget_amount,
    budget_currency: payload.budget_currency,
    capability: payload.capability,
    connector: payload.connector,
    content: payload.content,
    expires_at: payload.expires_at,
    parameters: {
      amount: payload.parameters.amount,
      project_title: payload.parameters.project_title,
    },
    principal: payload.principal,
    recipient: payload.recipient,
  };
  return JSON.stringify(ordered);
}

export async function computeSha256Hex(input: string): Promise<string> {
  if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
    const encoder = new TextEncoder();
    const data = encoder.encode(input);
    const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }
  // Deterministic fallback when Web Crypto is unavailable
  let h1 = 0xdeadbeef ^ input.length;
  let h2 = 0x41c6ce57 ^ input.length;
  for (let i = 0, ch: number; i < input.length; i++) {
    ch = input.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  const hex = (n: number) => (n >>> 0).toString(16).padStart(8, '0');
  return (hex(h1) + hex(h2)).repeat(4);
}
