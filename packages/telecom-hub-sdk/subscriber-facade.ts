/**
 * @agencyos/telecom-hub-sdk — Subscriber Management & Usage Billing Facade
 *
 * Provides unified interface for telecom subscriber lifecycle management,
 * plan assignment, usage tracking (voice/data/SMS), and billing operations.
 */

export interface Subscriber {
  id: string;
  msisdn: string;
  planId: string;
  status: 'active' | 'suspended' | 'terminated' | 'porting';
  dataUsage: DataUsage;
  balance: number;
  currency: string;
  activatedAt: string;
  expiresAt?: string;
}

export interface DataUsage {
  dataBytes: number;
  dataLimitBytes: number;
  voiceMinutes: number;
  voiceLimit: number;
  smsCount: number;
  smsLimit: number;
  periodStart: string;
  periodEnd: string;
}

export interface UsageRecord {
  subscriberId: string;
  type: 'voice' | 'data' | 'sms' | 'roaming';
  quantity: number;
  unit: 'bytes' | 'seconds' | 'count';
  timestamp: string;
  cost: number;
  destination?: string;
}

export interface TelecomPlan {
  id: string;
  name: string;
  dataLimitBytes: number;
  voiceMinutes: number;
  smsCount: number;
  monthlyFee: number;
  currency: string;
  roamingEnabled: boolean;
  features: string[];
}

export interface Invoice {
  id: string;
  subscriberId: string;
  period: string;
  lineItems: InvoiceLineItem[];
  total: number;
  currency: string;
  status: 'draft' | 'issued' | 'paid' | 'overdue';
  dueDate: string;
}

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export function createSubscriberManager() {
  return {
    getSubscriber: async (_subscriberId: string) => ({} as Subscriber),
    findByMsisdn: async (_msisdn: string) => ({} as Subscriber),
    changePlan: async (_subscriberId: string, _planId: string) => ({ success: true, effectiveDate: '' }),
    suspend: async (_subscriberId: string, _reason: string) => ({ success: true }),
    reactivate: async (_subscriberId: string) => ({ success: true }),
    getUsage: async (_subscriberId: string) => ({} as DataUsage),
  };
}

export function createUsageBilling() {
  return {
    recordUsage: async (_record: Omit<UsageRecord, 'cost'>) => ({ cost: 0 }),
    getUsageHistory: async (_subscriberId: string, _since: string) => [] as UsageRecord[],
    generateInvoice: async (_subscriberId: string, _period: string) => ({} as Invoice),
    getInvoices: async (_subscriberId: string) => [] as Invoice[],
    listPlans: async () => [] as TelecomPlan[],
  };
}
