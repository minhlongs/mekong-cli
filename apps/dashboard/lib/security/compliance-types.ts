/**
 * Data Privacy Compliance Types & Regional Rules (PDPA/GDPR)
 */

export interface JobPayload {
  requestId: string
  jobToken: string
  userId?: string
  jobType: string
  queuedAt: string
  expiresAt: string
  [key: string]: unknown
}

export interface SecureJob {
  id: string
  type: string
  payload: JobPayload
  jobToken: string
  userId?: string
  queuedAt: string
  expiresAt: string
  attempts: number
  maxAttempts: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
}

export type ConsentType =
  | 'marketing'
  | 'analytics'
  | 'personalization'
  | 'third_party'
  | 'essential'

export interface UserConsent {
  userId: string
  consents: Record<ConsentType, boolean>
  updatedAt: Date
  ipAddress?: string
  userAgent?: string
}

export interface DataExportRequest {
  id: string
  userId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  requestedAt: Date
  completedAt?: Date
  downloadUrl?: string
  expiresAt?: Date
}

export interface DataDeletionRequest {
  id: string
  userId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  requestedAt: Date
  completedAt?: Date
  tablesDeleted?: string[]
}

export type ComplianceRegulation = 'GDPR' | 'PDPA_TH' | 'PDPA_SG' | 'UU_PDP' | 'DPA_PH'

export interface RegulationRule {
  name: string
  country: string[]
  dataRetentionDays: number
  requiresExplicitConsent: boolean
  rightToErasure: boolean
  rightToPortability: boolean
  breachNotificationHours: number
}

export const COMPLIANCE_RULES: Record<ComplianceRegulation, RegulationRule> = {
  GDPR: {
    name: 'General Data Protection Regulation',
    country: ['EU', 'EEA'],
    dataRetentionDays: 365 * 3,
    requiresExplicitConsent: true,
    rightToErasure: true,
    rightToPortability: true,
    breachNotificationHours: 72,
  },
  PDPA_TH: {
    name: 'Personal Data Protection Act (Thailand)',
    country: ['TH'],
    dataRetentionDays: 365 * 5,
    requiresExplicitConsent: true,
    rightToErasure: true,
    rightToPortability: true,
    breachNotificationHours: 72,
  },
  PDPA_SG: {
    name: 'Personal Data Protection Act (Singapore)',
    country: ['SG'],
    dataRetentionDays: 365 * 5,
    requiresExplicitConsent: true,
    rightToErasure: false,
    rightToPortability: true,
    breachNotificationHours: 72,
  },
  UU_PDP: {
    name: 'Undang-Undang Perlindungan Data Pribadi (Indonesia)',
    country: ['ID'],
    dataRetentionDays: 365 * 5,
    requiresExplicitConsent: true,
    rightToErasure: true,
    rightToPortability: true,
    breachNotificationHours: 72,
  },
  DPA_PH: {
    name: 'Data Privacy Act (Philippines)',
    country: ['PH'],
    dataRetentionDays: 365 * 5,
    requiresExplicitConsent: true,
    rightToErasure: true,
    rightToPortability: true,
    breachNotificationHours: 72,
  },
}
