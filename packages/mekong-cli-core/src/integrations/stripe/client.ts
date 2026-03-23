/** Stripe integration — invoicing, payments, balance via stripe npm package */
import Stripe from 'stripe';
import type { Integration, IntegrationCredentials } from '../types.js';
import type { RevenueEntry } from '../../finance/types.js';
import { ok, err } from '../../types/common.js';
import type { Result } from '../../types/common.js';

export interface InvoiceLineItem {
  description: string;
  quantity: number;
  unitAmount: number; // cents
  currency: string;
}

export interface CreateInvoiceParams {
  customerEmail: string;
  customerName?: string;
  items: InvoiceLineItem[];
  daysUntilDue?: number;
  currency?: string;
}

export class StripeIntegration implements Integration {
  readonly name = 'stripe';
  connected = false;
  private client: Stripe | null = null;

  async connect(credentials: IntegrationCredentials): Promise<Result<void>> {
    if (credentials.type !== 'api_key') {
      return err(new Error('Stripe requires api_key credentials'));
    }
    try {
      this.client = new Stripe(credentials.key, { apiVersion: '2026-02-25.clover' });
      await this.client.balance.retrieve();
      this.connected = true;
      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async disconnect(): Promise<void> {
    this.client = null;
    this.connected = false;
  }

  async healthCheck(): Promise<boolean> {
    if (!this.client) return false;
    try {
      await this.client.balance.retrieve();
      return true;
    } catch {
      return false;
    }
  }

  async createInvoice(params: CreateInvoiceParams): Promise<Result<string>> {
    if (!this.client) return err(new Error('Not connected'));
    try {
      // Find or create customer
      const existing = await this.client.customers.list({ email: params.customerEmail, limit: 1 });
      let customerId: string;
      if (existing.data.length > 0) {
        customerId = existing.data[0].id;
      } else {
        const customer = await this.client.customers.create({
          email: params.customerEmail,
          name: params.customerName,
        });
        customerId = customer.id;
      }

      // Create invoice
      const invoice = await this.client.invoices.create({
        customer: customerId,
        collection_method: 'send_invoice',
        days_until_due: params.daysUntilDue ?? 30,
        currency: params.currency ?? 'usd',
      });

      // Add line items (amount = unit_amount * quantity in cents)
      for (const item of params.items) {
        await this.client.invoiceItems.create({
          customer: customerId,
          invoice: invoice.id,
          description: item.description,
          quantity: item.quantity,
          amount: item.unitAmount * item.quantity,
          currency: item.currency ?? params.currency ?? 'usd',
        });
      }

      return ok(invoice.id);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async sendInvoice(stripeInvoiceId: string): Promise<Result<void>> {
    if (!this.client) return err(new Error('Not connected'));
    try {
      await this.client.invoices.finalizeInvoice(stripeInvoiceId);
      await this.client.invoices.sendInvoice(stripeInvoiceId);
      return ok(undefined);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getPaymentStatus(stripeInvoiceId: string): Promise<Result<string>> {
    if (!this.client) return err(new Error('Not connected'));
    try {
      const invoice = await this.client.invoices.retrieve(stripeInvoiceId);
      return ok(invoice.status ?? 'unknown');
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async listRecentPayments(days: number): Promise<Result<RevenueEntry[]>> {
    if (!this.client) return err(new Error('Not connected'));
    try {
      const since = Math.floor(Date.now() / 1000) - days * 86400;
      const charges = await this.client.charges.list({ created: { gte: since }, limit: 100 });
      const entries: RevenueEntry[] = charges.data
        .filter(c => c.paid && c.status === 'succeeded')
        .map(c => ({
          id: c.id,
          customerId: typeof c.customer === 'string' ? c.customer : (c.customer?.id ?? 'unknown'),
          amount: c.amount / 100,
          currency: c.currency.toUpperCase(),
          type: 'one_time' as const,
          description: c.description ?? 'Stripe charge',
          date: new Date(c.created * 1000).toISOString().split('T')[0],
          stripePaymentId: c.id,
          createdAt: new Date(c.created * 1000).toISOString(),
        }));
      return ok(entries);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getBalance(): Promise<Result<{ available: number; pending: number; currency: string }>> {
    if (!this.client) return err(new Error('Not connected'));
    try {
      const balance = await this.client.balance.retrieve();
      const avail = balance.available[0];
      const pend = balance.pending[0];
      return ok({
        available: (avail?.amount ?? 0) / 100,
        pending: (pend?.amount ?? 0) / 100,
        currency: (avail?.currency ?? 'usd').toUpperCase(),
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
