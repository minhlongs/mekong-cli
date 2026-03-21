/**
 * System resource — health checks, status page, public stats, onboarding,
 * alerts, webhooks admin, licenses
 */

import type { HttpRequester } from '../http-requester.js';
import type {
  Alert, WebhookLog, License,
  CreateLicenseParams, ActivateLicenseResponse,
  OnboardingChecklist, OnboardingStep,
  AnalyticsStats, PublicStats,
  SystemStatus, Incident, HealthResponse, WaitlistResponse,
  Mission,
} from '../types.js';

export class HealthResource {
  constructor(private readonly http: HttpRequester) {}

  check(): Promise<HealthResponse> {
    return this.http.get('/health');
  }

  deep(): Promise<HealthResponse & { checks: Record<string, string> }> {
    return this.http.get('/health/deep');
  }
}

export class StatusResource {
  constructor(private readonly http: HttpRequester) {}

  get(): Promise<SystemStatus> {
    return this.http.get('/status');
  }

  getIncidents(): Promise<Incident[]> {
    return this.http.get('/status/incidents');
  }

  getHistory(): Promise<{ date: string; uptime_pct: number }[]> {
    return this.http.get('/status/history');
  }
}

export class AlertsResource {
  constructor(private readonly http: HttpRequester) {}

  list(): Promise<Alert[]> {
    return this.http.get('/v1/alerts');
  }

  getCount(): Promise<{ unread: number }> {
    return this.http.get('/v1/alerts/count');
  }
}

export class OnboardingResource {
  constructor(private readonly http: HttpRequester) {}

  getChecklist(): Promise<OnboardingChecklist> {
    return this.http.get('/v1/onboarding/checklist');
  }

  completeStep(step: string): Promise<OnboardingStep> {
    return this.http.post('/v1/onboarding/complete', { step });
  }

  getTips(): Promise<{ tips: string[] }> {
    return this.http.get('/v1/onboarding/tips');
  }
}

export class WebhooksAdminResource {
  constructor(private readonly http: HttpRequester) {}

  getLogs(): Promise<WebhookLog[]> {
    return this.http.get('/admin/webhooks/logs');
  }

  getDeadLetter(): Promise<WebhookLog[]> {
    return this.http.get('/admin/webhooks/dead-letter');
  }

  retry(id: string): Promise<{ success: boolean }> {
    return this.http.post(`/admin/webhooks/retry/${id}`);
  }

  getStats(): Promise<{ total: number; success: number; failed: number }> {
    return this.http.get('/admin/webhooks/stats');
  }
}

export class LicensesResource {
  constructor(private readonly http: HttpRequester) {}

  create(params: CreateLicenseParams): Promise<License> {
    return this.http.post('/v1/licenses', params);
  }

  list(): Promise<License[]> {
    return this.http.get('/v1/licenses');
  }

  verify(key: string): Promise<{ valid: boolean; license?: License }> {
    return this.http.get(`/v1/licenses/verify/${key}`);
  }

  activate(key: string): Promise<ActivateLicenseResponse> {
    return this.http.post(`/v1/licenses/activate/${key}`);
  }
}

export class AnalyticsResource {
  constructor(private readonly http: HttpRequester) {}

  getStats(): Promise<AnalyticsStats> {
    return this.http.get('/v1/analytics');
  }
}

export class PublicResource {
  constructor(private readonly http: HttpRequester) {}

  getStats(): Promise<PublicStats> {
    return this.http.get('/stats');
  }

  joinWaitlist(email: string, source?: string): Promise<WaitlistResponse> {
    return this.http.post('/waitlist', { email, source });
  }

  getMissionShare(id: string): Promise<Mission> {
    return this.http.get(`/share/${id}`);
  }
}
