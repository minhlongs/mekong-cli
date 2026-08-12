/**
 * Tenants resource — profile, settings, API keys, usage, invoices
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  Tenant, ApiKey,
  SignupParams, SignupResponse,
  UpdateTenantSettingsParams,
  CreateApiKeyParams, CreateApiKeyResponse,
  CreditTransaction, PaginatedResponse,
} from '../types.js';

export class TenantsResource {
  constructor(private readonly http: HttpRequester) {}

  /** Create account — returns JWT + 10 credits */
  signup(params: SignupParams): Promise<SignupResponse> {
    return this.http.post('/v1/tenants/signup', params);
  }

  getProfile(): Promise<Tenant> {
    return this.http.get('/v1/tenants/profile');
  }

  updateSettings(params: UpdateTenantSettingsParams): Promise<Tenant> {
    return this.http.put('/v1/tenants/settings', params);
  }

  createApiKey(params?: CreateApiKeyParams): Promise<CreateApiKeyResponse> {
    return this.http.post('/v1/tenants/api-keys', params);
  }

  listApiKeys(): Promise<ApiKey[]> {
    return this.http.get('/v1/tenants/api-keys');
  }

  revokeApiKey(id: string): Promise<{ success: boolean }> {
    return this.http.del(`/v1/tenants/api-keys/${id}`);
  }

  getUsage(): Promise<{ period: string; missions: number; credits_spent: number }> {
    return this.http.get('/v1/tenants/usage');
  }

  getInvoices(params?: {
    limit?: number;
    offset?: number;
    type?: string;
  }): Promise<PaginatedResponse<CreditTransaction>> {
    return this.http.get('/v1/tenants/invoices', params);
  }

  extendTrial(): Promise<{ success: boolean; message: string }> {
    return this.http.post('/v1/tenants/trial-extend');
  }
}
