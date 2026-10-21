/**
 * Onboarding Flow Types & Constants for Beta RaaS Gateway
 */

export interface OnboardingState {
  tenant_id: string
  email_verified: boolean
  welcome_email_sent: boolean
  onboarding_step: number
  onboarding_completed: boolean
  first_command_run: boolean
  tutorial_step: number
  tutorial_completed: boolean
  feedback_submitted: boolean
  nps_score: number | null
  created_at: string
  updated_at: string
}

export interface UsageMilestone {
  tenant_id: string
  tier_name: string
  tier_limit: number
  current_usage: number
  usage_percent: number
  milestone_reached: 10 | 50 | 80 | 100 | null
  emails_sent: {
    milestone_10: boolean
    milestone_50: boolean
    milestone_80: boolean
    milestone_100: boolean
  }
}

export interface FeedbackEntry {
  id: string
  tenant_id: string
  type: 'nps' | 'feature' | 'general'
  score: number | null
  feedback: string
  category?: string
  created_at: string
}

export interface TutorialProgress {
  tenant_id: string
  current_step: number
  total_steps: number
  completed_steps: number[]
  started_at: string
  completed_at: string | null
}

export const TUTORIAL_STEPS = [
  { id: 1, name: 'setup_profile', title: 'Set up your profile', description: 'Complete your business profile' },
  { id: 2, name: 'connect_channel', title: 'Connect a channel', description: 'Link your first communication channel' },
  { id: 3, name: 'explore_commands', title: 'Explore commands', description: 'Browse available commands' },
  { id: 4, name: 'run_first_command', title: 'Run your first command', description: 'Execute /cook to build something' },
  { id: 5, name: 'review_result', title: 'Review results', description: 'Check your command output' },
] as const

export function generateVerificationCode(): string {
  return Math.floor(100000 + Math.random() * 900000).toString()
}

export function categorizeNpsScore(score: number): 'detractor' | 'passive' | 'promoter' {
  if (score <= 6) return 'detractor'
  if (score <= 8) return 'passive'
  return 'promoter'
}
