"""Onboarding progress bar component.

Displays user's progress through the onboarding funnel with step indicators.

Usage:
    <OnboardingProgressBar currentStep="llm_config" steps={ONBOARDING_STEPS} />

Task #299: Implement Dashboard Onboarding UI Components
Status: In Progress
"""
from React from "react";

interface Step {
  id: string;
  title: string;
  description?: string;
}

interface OnboardingProgressBarProps {
  currentStep: string;
  steps: Step[];
  className?: string;
}

export function OnboardingProgressBar({
  currentStep,
  steps,
  className = "",
}: OnboardingProgressBarProps) {
  const currentIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <nav className={`mb-8 ${className}`} aria-label="Onboarding progress">
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentIndex;
          const isCurrent = step.id === currentStep;
          const isUpcoming = index > currentIndex;

          return (
            <li key={step.id} className="flex items-center flex-1">
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 rounded-full ${
                    isCompleted ? "bg-green-500" : "bg-gray-200 dark:bg-gray-700"
                  }`}
                />
              )}

              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                    isCompleted
                      ? "bg-green-500 text-white"
                      : isCurrent
                      ? "bg-blue-500 text-white ring-4 ring-blue-200 dark:ring-blue-800"
                      : "bg-gray-200 text-gray-500 dark:bg-gray-700"
                  }`}
                >
                  {isCompleted ? "✓" : index + 1}
                </div>
                <div className="mt-2 text-center">
                  <div
                    className={`text-sm font-medium ${
                      isCurrent
                        ? "text-blue-600 dark:text-blue-400"
                        : isCompleted
                        ? "text-green-600 dark:text-green-400"
                        : "text-gray-500 dark:text-gray-400"
                    }`}
                  >
                    {step.title}
                  </div>
                  {step.description && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-[120px]">
                      {step.description}
                    </div>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// Onboarding step definitions
export const ONBOARDING_STEPS: Step[] = [
  {
    id: "welcome",
    title: "Welcome",
    description: "Get started",
  },
  {
    id: "llm_config",
    title: "AI Provider",
    description: "Connect LLM",
  },
  {
    id: "founder_profile",
    title: "Profile",
    description: "Your preferences",
  },
  {
    id: "tutorial",
    title: "Tutorial",
    description: "First mission",
  },
  {
    id: "complete",
    title: "Complete",
    description: "You're ready!",
  },
];
