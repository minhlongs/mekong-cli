/**
 * Onboarding Flow Logic for Beta RaaS Gateway
 * Handles: Signup flow, First command tutorial, Usage milestones, Feedback collection
 */

export {
  type OnboardingState,
  type UsageMilestone,
  type FeedbackEntry,
  type TutorialProgress,
  TUTORIAL_STEPS,
  categorizeNpsScore,
} from './flows-types'

export {
  initializeOnboarding,
  verifyEmail,
  markWelcomeEmailSent,
  getOnboardingState,
  initializeTutorial,
  completeTutorialStep,
  getTutorialProgress,
} from './flows-steps'

export {
  initializeUsageTracking,
  updateUsageAndCheckMilestones,
  markMilestoneEmailSent,
  getUsageMilestoneStatus,
  submitNpsScore,
  submitFeedback,
  getFeedbackEntries,
  getAllFeedbackEntries,
  getAverageNpsScore,
} from './flows-progress'
