/**
 * PayOS-specific webhook data types
 *
 * Raw data structures from PayOS Vietnamese QR gateway webhooks.
 * Extracted from @agencyos/vibe-payment/payos-adapter for reuse.
 */

/** Raw PayOS webhook payload data */
export interface PayOSWebhookData {
  orderCode: number;
  amount: number;
  description: string;
  accountNumber: string;
  reference: string;
  transactionDateTime: string;
  currency: string;
  paymentLinkId: string;
  code: string;
  desc: string;
  counterAccountBankId?: string;
  counterAccountBankName?: string;
  counterAccountName?: string;
  counterAccountNumber?: string;
  virtualAccountName?: string;
  virtualAccountNumber?: string;
}

/** PayOS webhook envelope (wraps data + signature) */
export interface PayOSWebhookPayload {
  data: PayOSWebhookData;
  signature: string;
}

/** PayOS transaction code meanings */
export type PayOSTransactionCode = '00' | '01' | string;

/** Map PayOS code → human-readable status */
export const PAYOS_CODE_MAP: Record<string, string> = {
  '00': 'PAID',
  '01': 'CANCELLED',
} as const;
