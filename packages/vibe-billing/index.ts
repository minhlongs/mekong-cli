/**
 * @agencyos/vibe-billing — Billing Facade SDK
 *
 * Higher-level billing operations built on top of @agencyos/billing primitives.
 * Invoicing, discount engine, tax calculation, payment lifecycle hooks, refund management.
 *
 * Usage:
 *   import { createInvoiceEngine, createDiscountEngine, createTaxCalculator } from '@agencyos/vibe-billing';
 *   const invoices = createInvoiceEngine({ currency: 'VND', taxRate: 0.08 });
 *   const discounts = createDiscountEngine();
 *   const tax = createTaxCalculator({ defaultRate: 0.08 });
 */

// ─── Types ──────────────────────────────────────────────────────

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled' | 'refunded';
export type DiscountType = 'percentage' | 'fixed' | 'bogo' | 'tiered';
export type RefundReason = 'customer_request' | 'defective' | 'not_received' | 'duplicate' | 'other';

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unitPrice: number;
  taxRate?: number;
  discountAmount?: number;
}

export interface Invoice {
  id: string;
  number: string;
  status: InvoiceStatus;
  customerName: string;
  customerEmail: string;
  items: InvoiceLineItem[];
  subtotal: number;
  taxTotal: number;
  discountTotal: number;
  total: number;
  currency: string;
  issuedAt: string;
  dueDate: string;
  paidAt?: string;
}

export interface Discount {
  id: string;
  code: string;
  type: DiscountType;
  value: number; // percentage (0-100) or fixed amount
  minOrderAmount?: number;
  maxUses?: number;
  currentUses: number;
  validFrom: string;
  validUntil: string;
  applicableProducts?: string[];
}

export interface RefundRequest {
  invoiceId: string;
  amount: number;
  reason: RefundReason;
  notes?: string;
}

// ─── Invoice Engine ─────────────────────────────────────────────

export interface InvoiceEngineConfig {
  currency: string;
  taxRate: number;
  invoicePrefix?: string;
  dueDays?: number;
}

export function createInvoiceEngine(config: InvoiceEngineConfig) {
  const { currency, taxRate, invoicePrefix = 'INV', dueDays = 30 } = config;
  let counter = 0;

  return {
    /**
     * Generate invoice number: INV-2026-0001
     */
    generateNumber(): string {
      counter++;
      const year = new Date().getFullYear();
      return `${invoicePrefix}-${year}-${String(counter).padStart(4, '0')}`;
    },

    /**
     * Tính tổng invoice từ line items
     */
    calculateTotals(items: InvoiceLineItem[]): { subtotal: number; taxTotal: number; discountTotal: number; total: number } {
      let subtotal = 0;
      let taxTotal = 0;
      let discountTotal = 0;

      for (const item of items) {
        const lineTotal = item.quantity * item.unitPrice;
        const lineDiscount = item.discountAmount ?? 0;
        const lineTax = Math.round((lineTotal - lineDiscount) * (item.taxRate ?? taxRate));
        subtotal += lineTotal;
        taxTotal += lineTax;
        discountTotal += lineDiscount;
      }

      return { subtotal, taxTotal, discountTotal, total: subtotal + taxTotal - discountTotal };
    },

    /**
     * Tính due date từ ngày issue
     */
    calculateDueDate(issuedAt: Date): Date {
      const due = new Date(issuedAt);
      due.setDate(due.getDate() + dueDays);
      return due;
    },

    /**
     * Check invoice overdue
     */
    isOverdue(invoice: Invoice): boolean {
      if (invoice.status === 'paid' || invoice.status === 'cancelled') return false;
      return new Date() > new Date(invoice.dueDate);
    },

    /**
     * Format currency
     */
    formatAmount(amount: number): string {
      return new Intl.NumberFormat('vi-VN', { style: 'currency', currency }).format(amount);
    },
  };
}

// ─── Discount Engine ────────────────────────────────────────────

export function createDiscountEngine() {
  return {
    /**
     * Validate discount code
     */
    validateDiscount(discount: Discount, orderAmount: number): { valid: boolean; reason?: string } {
      const now = new Date();
      if (now < new Date(discount.validFrom)) return { valid: false, reason: 'Mã giảm giá chưa có hiệu lực' };
      if (now > new Date(discount.validUntil)) return { valid: false, reason: 'Mã giảm giá đã hết hạn' };
      if (discount.maxUses && discount.currentUses >= discount.maxUses) return { valid: false, reason: 'Mã giảm giá đã hết lượt sử dụng' };
      if (discount.minOrderAmount && orderAmount < discount.minOrderAmount) {
        return { valid: false, reason: `Đơn hàng tối thiểu ${discount.minOrderAmount}` };
      }
      return { valid: true };
    },

    /**
     * Tính discount amount
     */
    calculateDiscount(discount: Discount, orderAmount: number): number {
      switch (discount.type) {
        case 'percentage':
          return Math.round(orderAmount * (discount.value / 100));
        case 'fixed':
          return Math.min(discount.value, orderAmount);
        case 'bogo':
          return 0; // handled at item level
        case 'tiered':
          return 0; // handled by tiered pricing logic
        default:
          return 0;
      }
    },
  };
}

// ─── Tax Calculator ─────────────────────────────────────────────

export interface TaxRule {
  region: string;
  rate: number;
  name: string;
  inclusive: boolean;
}

export function createTaxCalculator(config: { defaultRate: number }) {
  const { defaultRate } = config;

  return {
    /**
     * Tính tax cho amount
     */
    calculateTax(amount: number, rate?: number): { taxAmount: number; totalWithTax: number } {
      const effectiveRate = rate ?? defaultRate;
      const taxAmount = Math.round(amount * effectiveRate);
      return { taxAmount, totalWithTax: amount + taxAmount };
    },

    /**
     * Extract tax từ tax-inclusive price
     */
    extractInclusiveTax(totalWithTax: number, rate?: number): { netAmount: number; taxAmount: number } {
      const effectiveRate = rate ?? defaultRate;
      const netAmount = Math.round(totalWithTax / (1 + effectiveRate));
      return { netAmount, taxAmount: totalWithTax - netAmount };
    },
  };
}

// ─── Refund Engine ──────────────────────────────────────────────

export function createRefundEngine() {
  return {
    /**
     * Validate refund request
     */
    validateRefund(invoice: Invoice, request: RefundRequest): { valid: boolean; reason?: string } {
      if (invoice.status !== 'paid') return { valid: false, reason: 'Chỉ refund được invoice đã thanh toán' };
      if (request.amount > invoice.total) return { valid: false, reason: 'Số tiền refund vượt quá tổng invoice' };
      if (request.amount <= 0) return { valid: false, reason: 'Số tiền refund phải lớn hơn 0' };
      return { valid: true };
    },

    /**
     * Check if partial refund
     */
    isPartialRefund(invoice: Invoice, refundAmount: number): boolean {
      return refundAmount < invoice.total;
    },
  };
}
