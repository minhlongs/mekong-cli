/**
 * Email Template Types & Shared Styles for Beta Onboarding Flow
 */

export interface EmailTemplate {
  subject: string
  html: string
  text: string
}

export interface WelcomeEmailData {
  tenantName: string
  businessName: string
  apiKey: string
  dashboardUrl: string
  docsUrl: string
}

export interface VerificationEmailData {
  email: string
  verificationCode: string
  verificationUrl: string
}

export interface TutorialEmailData {
  tenantName: string
  tutorialStep: number
  totalSteps: number
  tutorialUrl: string
}

export interface MilestoneEmailData {
  tenantName: string
  usagePercent: number
  currentUsage: number
  tierLimit: number
  tierName: string
  upgradeUrl: string
}

export interface FeedbackEmailData {
  tenantName: string
  feedbackUrl: string
  npsSurveyUrl: string
}

export interface SetupReminderEmailData {
  tenantName: string
  businessName: string
  setupUrl: string
}
