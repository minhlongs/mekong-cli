/**
 * MekongClient — entry point for all RaaS Gateway API calls
 * Composes resource classes via shared HttpRequester
 */

import { HttpRequester } from './http-requester.js';
import { MissionsResource } from './resources/missions-resource.js';
import { TenantsResource } from './resources/tenants-resource.js';
import { CreditsResource } from './resources/credits-resource.js';
import { BillingResource } from './resources/billing-resource.js';
import { MarketplaceResource } from './resources/marketplace-resource.js';
import {
  HealthResource,
  StatusResource,
  AlertsResource,
  OnboardingResource,
  WebhooksAdminResource,
  LicensesResource,
  AnalyticsResource,
  PublicResource,
} from './resources/system-resource.js';

export interface MekongClientConfig {
  /** API base URL (default: production gateway) */
  baseUrl?: string;
  /** API key auth — sends X-API-Key header */
  apiKey?: string;
  /** JWT auth — sends Authorization: Bearer header */
  jwt?: string;
  /** Max retry attempts on 5xx/network errors (default: 3) */
  maxRetries?: number;
  /** Request timeout in ms (default: 30000) */
  timeoutMs?: number;
}

const DEFAULT_BASE_URL = 'https://raas-gateway.agencyos-openclaw.workers.dev';

export class MekongClient {
  private _jwt: string | undefined;
  private readonly _apiKey: string | undefined;

  readonly missions: MissionsResource;
  readonly tenants: TenantsResource;
  readonly credits: CreditsResource;
  readonly billing: BillingResource;
  readonly marketplace: MarketplaceResource;
  readonly health: HealthResource;
  readonly status: StatusResource;
  readonly alerts: AlertsResource;
  readonly onboarding: OnboardingResource;
  readonly webhooks: WebhooksAdminResource;
  readonly licenses: LicensesResource;
  readonly analytics: AnalyticsResource;
  readonly public: PublicResource;

  constructor(config: MekongClientConfig = {}) {
    this._jwt = config.jwt;
    this._apiKey = config.apiKey;

    const http = new HttpRequester({
      baseUrl: config.baseUrl ?? DEFAULT_BASE_URL,
      getJwt: () => this._jwt,
      getApiKey: () => this._apiKey,
      maxRetries: config.maxRetries ?? 3,
      timeoutMs: config.timeoutMs ?? 30_000,
    });

    this.missions = new MissionsResource(http);
    this.tenants = new TenantsResource(http);
    this.credits = new CreditsResource(http);
    this.billing = new BillingResource(http);
    this.marketplace = new MarketplaceResource(http);
    this.health = new HealthResource(http);
    this.status = new StatusResource(http);
    this.alerts = new AlertsResource(http);
    this.onboarding = new OnboardingResource(http);
    this.webhooks = new WebhooksAdminResource(http);
    this.licenses = new LicensesResource(http);
    this.analytics = new AnalyticsResource(http);
    this.public = new PublicResource(http);
  }

  /** Update JWT after signup/login — applies to all subsequent requests */
  setJwt(token: string): void {
    this._jwt = token;
  }
}
