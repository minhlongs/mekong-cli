/**
 * Email Templates for Beta Onboarding Flow
 * Supports: Welcome, Verification, Milestone, Feedback, NPS surveys
 */

export type {
  EmailTemplate,
  WelcomeEmailData,
  VerificationEmailData,
  TutorialEmailData,
  MilestoneEmailData,
  FeedbackEmailData,
  SetupReminderEmailData,
} from './templates-types'

export { createWelcomeEmail, createVerificationEmail } from './templates-welcome'
export { createTutorialEmail, createMilestoneEmail } from './templates-billing'
export { createFeedbackEmail, createSetupReminderEmail } from './templates-alerts'
