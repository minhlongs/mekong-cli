/**
 * RaaS Open Core License Gating
 *
 * Premium agents gated behind RAAS_LICENSE_KEY verification.
 * Core CLI, commands, skills remain open-source.
 */

// License verification via environment variable
const RAAS_LICENSE_KEY = process.env.RAAS_LICENSE_KEY;

/**
 * Check if RaaS license is valid
 */
export function hasValidLicense(): boolean {
  return !!RAAS_LICENSE_KEY && RAAS_LICENSE_KEY.length > 0;
}

/**
 * Require valid license for premium features
 * Throws error if license is missing or invalid
 */
export function requireLicense(featureName: string): void {
  if (!hasValidLicense()) {
    throw new Error(
      `RaaS License Required: "${featureName}" is a premium feature.\n` +
      `Set RAAS_LICENSE_KEY environment variable to access.\n` +
      `Contact: licensing@mekong-cli.dev`
    );
  }
}

/**
 * Premium agents that require license
 */
export const PREMIUM_AGENTS = {
  // CTO Auto-Pilot - Phase 1
  "auto-cto-pilot": {
    name: "CTO Auto-Pilot",
    description: "Tự động tạo tasks chất lượng cao theo Binh Pháp",
    phase: "discovery",
  },
  // Opus-gated features
  "opus-strategy": {
    name: "Opus Strategy",
    description: "Strategic planning với Claude Opus 4.6",
    phase: "planning",
  },
  "opus-parallel": {
    name: "Opus Parallel",
    description: "Parallel agent orchestration với Opus",
    phase: "building",
  },
  "opus-review": {
    name: "Opus Code Review",
    description: "Security & quality review với Opus",
    phase: "polish",
  },
} as const;

export type PremiumAgentKey = keyof typeof PREMIUM_AGENTS;

/**
 * Check if specific agent is premium
 */
export function isPremiumAgent(agentName: string): boolean {
  return agentName in PREMIUM_AGENTS;
}

/**
 * Gate access to premium agent
 */
export function requirePremiumAgent(agentName: string): void {
  if (isPremiumAgent(agentName)) {
    const agent = PREMIUM_AGENTS[agentName as PremiumAgentKey];
    requireLicense(agent.name);
  }
}

/**
 * Get list of available agents based on license status
 */
export function getAvailableAgents(): {
  available: string[];
  premium: string[];
  locked: string[];
} {
  const hasLicense = hasValidLicense();

  // Core agents (always available)
  const coreAgents = [
    "planner",
    "fullstack-developer",
    "code-reviewer",
    "tester",
    "debugger",
    "researcher",
    "ui-ux-designer",
    "docs-manager",
    "project-manager",
    "git-manager",
  ];

  // Premium agents
  const premiumAgents = Object.keys(PREMIUM_AGENTS);

  return {
    available: coreAgents,
    premium: premiumAgents,
    locked: hasLicense ? [] : premiumAgents,
  };
}
