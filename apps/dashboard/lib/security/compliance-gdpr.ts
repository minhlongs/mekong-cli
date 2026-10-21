/**
 * GDPR / PDPA Compliance Service Implementation
 */

import { createClient } from '@supabase/supabase-js'
import { securityLogger } from './logger'
import { SecureJobQueue } from './compliance-audit'
import {
  COMPLIANCE_RULES,
  type ComplianceRegulation,
  type ConsentType,
  type DataDeletionRequest,
  type DataExportRequest,
  type UserConsent,
} from './compliance-types'

export class ComplianceService {
  private supabase
  private secureJobQueue: SecureJobQueue

  constructor() {
    this.supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.SUPABASE_SERVICE_KEY!
    )
    this.secureJobQueue = new SecureJobQueue()
  }

  private generateJobToken(requestId: string, jobType: string): string {
    return this.secureJobQueue.generateJobToken(requestId, jobType)
  }

  async getConsent(userId: string): Promise<UserConsent | null> {
    const { data } = await this.supabase
      .from('user_consents')
      .select('*')
      .eq('user_id', userId)
      .single()

    if (!data) return null
    return { userId: data.user_id, consents: data.consents, updatedAt: new Date(data.updated_at) }
  }

  async updateConsent(
    userId: string,
    consents: Partial<Record<ConsentType, boolean>>,
    metadata?: { ipAddress?: string; userAgent?: string }
  ): Promise<void> {
    const existing = await this.getConsent(userId)
    const newConsents = { essential: true, ...existing?.consents, ...consents }

    await this.supabase.from('user_consents').upsert({
      user_id: userId,
      consents: newConsents,
      ip_address: metadata?.ipAddress,
      user_agent: metadata?.userAgent,
      updated_at: new Date().toISOString(),
    })

    await this.logConsentChange(userId, newConsents)
  }

  async hasConsent(userId: string, type: ConsentType): Promise<boolean> {
    const consent = await this.getConsent(userId)
    return consent?.consents[type] ?? false
  }

  private async logConsentChange(userId: string, consents: Record<string, boolean>): Promise<void> {
    await this.supabase.from('audit_logs').insert({
      user_id: userId,
      action: 'consent_update',
      resource_type: 'consent',
      details: { consents },
    })
  }

  async requestDataExport(userId: string): Promise<DataExportRequest> {
    const { data, error } = await this.supabase
      .from('data_export_requests')
      .insert({ user_id: userId, status: 'pending', requested_at: new Date().toISOString() })
      .select()
      .single()

    if (error) throw new Error(`Failed to create export request: ${error.message}`)
    await this.queueJob(data.id, 'data_export', 'Data export job queued securely', 'export')
    return { id: data.id, userId: data.user_id, status: data.status, requestedAt: new Date(data.requested_at) }
  }

  async getExportStatus(requestId: string): Promise<DataExportRequest | null> {
    const { data } = await this.supabase.from('data_export_requests').select('*').eq('id', requestId).single()
    if (!data) return null
    return {
      id: data.id,
      userId: data.user_id,
      status: data.status,
      requestedAt: new Date(data.requested_at),
      completedAt: data.completed_at ? new Date(data.completed_at) : undefined,
      downloadUrl: data.download_url,
      expiresAt: data.expires_at ? new Date(data.expires_at) : undefined,
    }
  }

  async requestDataDeletion(userId: string): Promise<DataDeletionRequest> {
    const { data, error } = await this.supabase
      .from('data_deletion_requests')
      .insert({ user_id: userId, status: 'pending', requested_at: new Date().toISOString() })
      .select()
      .single()

    if (error) throw new Error(`Failed to create deletion request: ${error.message}`)
    await this.queueJob(data.id, 'data_deletion', 'Data deletion job queued securely', 'deletion')
    return { id: data.id, userId: data.user_id, status: data.status, requestedAt: new Date(data.requested_at) }
  }

  async getDeletionStatus(requestId: string): Promise<DataDeletionRequest | null> {
    const { data } = await this.supabase.from('data_deletion_requests').select('*').eq('id', requestId).single()
    if (!data) return null
    return {
      id: data.id,
      userId: data.user_id,
      status: data.status,
      requestedAt: new Date(data.requested_at),
      completedAt: data.completed_at ? new Date(data.completed_at) : undefined,
      tablesDeleted: data.tables_deleted,
    }
  }

  private async queueJob(
    requestId: string,
    jobType: 'data_export' | 'data_deletion',
    logMessage: string,
    label: string
  ): Promise<void> {
    const jobToken = this.generateJobToken(requestId, jobType)
    try {
      await this.secureJobQueue.enqueue(jobType, {
        requestId,
        jobToken,
        userId: requestId,
        jobType,
        queuedAt: new Date().toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      })
      await securityLogger.security(jobType, logMessage, { requestId, jobToken: jobToken.substring(0, 10) + '***' })
    } catch (error) {
      await securityLogger.error(
        `Failed to queue ${label} job`,
        error instanceof Error ? error : new Error(String(error)),
        { requestId }
      )
      throw new Error(`Failed to queue ${label} job`)
    }
  }

  async getApplicableRegulation(countryCode: string): Promise<ComplianceRegulation> {
    for (const [regulation, rules] of Object.entries(COMPLIANCE_RULES)) {
      if (rules.country.includes(countryCode)) return regulation as ComplianceRegulation
    }
    return 'GDPR'
  }

  async cleanupExpiredData(regulation: ComplianceRegulation): Promise<number> {
    const rules = COMPLIANCE_RULES[regulation]
    const expiryDate = new Date()
    expiryDate.setDate(expiryDate.getDate() - rules.dataRetentionDays)
    const { count } = await this.supabase.from('usage_events').delete().lt('created_at', expiryDate.toISOString())
    return count || 0
  }
}

export const complianceService = new ComplianceService()
