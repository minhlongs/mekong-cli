"""Onboarding wizard page component.

Provides a multi-step onboarding flow for new users:
1. Welcome & vision
2. LLM provider configuration
3. Founder genome profiling
4. Tutorial mission
5. Completion

All steps are server components with client-side interactivity for forms and API calls.

Task #299: Implement Dashboard Onboarding UI Components
Status: In Progress
"""
"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { OnboardingProgressBar, ONBOARDING_STEPS } from "./OnboardingProgressBar";

interface OnboardingState {
  currentStep: string;
  completedSteps: string[];
  llmConfigured: boolean;
  profileCompleted: boolean;
  tutorialCompleted: boolean;
}

export default function OnboardingPage() {
  const router = useRouter();
  const [state, setState] = useState<OnboardingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Map API stage to step ID
  const mapStageToStep = (stage: string): string => {
    const mapping: Record<string, string> = {
      "signup_started": "welcome",
      "llm_configured": "llm_config",
      "llm_config": "llm_config",
      "founder_profile": "founder_profile",
      "tutorial": "tutorial",
      "first_mission_completed": "tutorial",
      "complete": "complete",
    };
    return mapping[stage] || "welcome";
  };

  // Load onboarding state on mount
  useEffect(() => {
    async function loadState() {
      try {
        const res = await fetch("/v1/onboarding/progress");
        if (res.ok) {
          const data = await res.json();
          const completedStages = data.completed_stages || [];
          setState({
            currentStep: mapStageToStep(data.current_stage),
            completedSteps: completedStages,
            llmConfigured: completedStages.includes("llm_configured") || completedStages.includes("llm_config"),
            profileCompleted: completedStages.includes("founder_profile"),
            tutorialCompleted: completedStages.includes("tutorial") || completedStages.includes("first_mission_completed"),
          });
        } else if (res.status === 404) {
          // No state yet - start fresh
          setState({
            currentStep: "welcome",
            completedSteps: [],
            llmConfigured: false,
            profileCompleted: false,
            tutorialCompleted: false,
          });
        }
      } catch (err) {
        console.error("Failed to load onboarding state:", err);
      } finally {
        setLoading(false);
      }
    }
    loadState();
  }, []);

  const currentIndex = state
    ? ONBOARDING_STEPS.findIndex((s) => s.id === state.currentStep)
    : -1;

  const renderStep = () => {
    if (!state) return null;

    switch (state.currentStep) {
      case "welcome":
        return <WelcomeStep state={state} onComplete={handleCompleteStep} />;
      case "llm_config":
        return <LLMConfigStep state={state} onComplete={handleCompleteStep} onSaving={setSaving} />;
      case "founder_profile":
        return <FounderProfileStep state={state} onComplete={handleCompleteStep} onSaving={setSaving} />;
      case "tutorial":
        return <TutorialStep state={state} onComplete={handleCompleteStep} />;
      case "complete":
        return <CompletionStep />;
      default:
        return <div>Unknown step</div>;
    }
  };

  async function handleCompleteStep(stepData?: Record<string, any>) {
    if (!state) return;
    setSaving(true);
    try {
      // Mark current step as completed via API with optional step data
      await fetch("/v1/onboarding/step", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step: state.currentStep, data: stepData || {} }),
      });
      // Move to next step
      const nextIndex = currentIndex + 1;
      if (nextIndex < ONBOARDING_STEPS.length) {
        const newCompletedSteps = [...state.completedSteps, state.currentStep];
        setState({
          ...state,
          currentStep: ONBOARDING_STEPS[nextIndex].id,
          completedSteps: newCompletedSteps,
          llmConfigured: newCompletedSteps.includes("llm_configured") || newCompletedSteps.includes("llm_config"),
          profileCompleted: newCompletedSteps.includes("founder_profile"),
          tutorialCompleted: newCompletedSteps.includes("tutorial") || newCompletedSteps.includes("first_mission_completed"),
        });
      }
    } catch (err) {
      console.error("Failed to save progress:", err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-indigo-950 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Welcome to Mekong IDE</h1>
          <p className="text-gray-400">Let's get you set up in about 5 minutes.</p>
        </header>

        {/* Progress bar */}
        <OnboardingProgressBar
          currentStep={state?.currentStep || "welcome"}
          steps={ONBOARDING_STEPS}
          className="mb-12"
        />

        {/* Step content */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-lg p-8 border border-gray-800">
            {renderStep()}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-gray-500 text-sm">
          <p>
            Need help? Check our{" "}
            <a href="/docs/onboarding" className="text-blue-400 hover:underline">
              documentation
            </a>{" "}
            or join our Discord community.
          </p>
        </footer>
      </div>
    </div>
  );
}

// ============================================================================
// Step Components
// ============================================================================

function WelcomeStep({
  state,
  onComplete,
}: {
  state: OnboardingState;
  onComplete: (data?: Record<string, any>) => void;
}) {
  const [businessType, setBusinessType] = useState<string>("");
  const [goal, setGoal] = useState<string>("");

  const handleContinue = () => {
    onComplete({ businessType, goal });
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">You're about to build your one-person company</h2>
      <p className="text-gray-300 mb-6">
        10 business layers. Zero employees. Full autonomy. Let's personalize your experience.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">What kind of business are you building?</label>
          <select
            value={businessType}
            onChange={(e) => setBusinessType(e.target.value)}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">Select a type...</option>
            <option value="saas">SaaS / Software</option>
            <option value="ecommerce">E-commerce</option>
            <option value="agency">Agency / Services</option>
            <option value="creator">Creator / Content</option>
            <option value="trading">Trading / Investing</option>
            <option value="consulting">Consulting</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Your primary goal for the next 90 days</label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          >
            <option value="">Select a goal...</option>
            <option value="launch-mvp">Launch MVP</option>
            <option value="get-customers">Get first customers</option>
            <option value="automate-ops">Automate operations</option>
            <option value="build-team">Build a team</option>
            <option value="scale-revenue">Scale revenue</option>
            <option value="explore-ideas">Explore ideas</option>
          </select>
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={handleContinue}
          disabled={!businessType || !goal}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function LLMConfigStep({
  state,
  onComplete,
  onSaving,
}: {
  state: OnboardingState;
  onComplete: (data?: Record<string, any>) => void;
  onSaving: (saving: boolean) => void;
}) {
  const [provider, setProvider] = useState<string>("anthropic");
  const [apiKey, setApiKey] = useState<string>("");
  const [model, setModel] = useState<string>("claude-sonnet-4");
  const [testStatus, setTestStatus] = useState<"idle" | "testing" | "success" | "error">("idle");

  const providers = [
    { id: "anthropic", name: "Anthropic Claude", defaultModel: "claude-sonnet-4" },
    { id: "openai", name: "OpenAI GPT", defaultModel: "gpt-4o" },
    { id: "openrouter", name: "OpenRouter", defaultModel: "anthropic/claude-sonnet-4" },
    { id: "ollama", name: "Ollama (local)", defaultModel: "llama3.2:3b" },
    { id: "custom", name: "Custom endpoint", defaultModel: "" },
  ];

  const selectedProvider = providers.find((p) => p.id === provider);

  const handleTest = async () => {
    setTestStatus("testing");
    try {
      const res = await fetch("/v1/onboarding/test-llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, apiKey, model }),
      });
      if (res.ok) {
        setTestStatus("success");
      } else {
        setTestStatus("error");
      }
    } catch (err) {
      setTestStatus("error");
    }
  };

  const handleContinue = async () => {
    onSaving(true);
    try {
      onComplete({ provider, apiKey: apiKey || undefined, model });
    } finally {
      onSaving(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Connect Your AI Brain</h2>
      <p className="text-gray-300 mb-6">
        Mekong works with any OpenAI-compatible API. Choose your provider.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">Provider</label>
          <select
            value={provider}
            onChange={(e) => {
              setProvider(e.target.value);
              const p = providers.find((prov) => prov.id === e.target.value);
              if (p) setModel(p.defaultModel);
            }}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>

        {provider !== "ollama" && (
          <div>
            <label className="block text-sm font-medium mb-2">API Key</label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium mb-2">Model</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={selectedProvider?.defaultModel}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <button
            type="button"
            onClick={handleTest}
            disabled={testStatus === "testing" || (provider !== "ollama" && !apiKey)}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {testStatus === "testing" ? "Testing..." : "Test Connection"}
          </button>
          {testStatus === "success" && <span className="ml-3 text-green-400">✓ Connected</span>}
          {testStatus === "error" && <span className="ml-3 text-red-400">✗ Failed</span>}
        </div>
      </div>

      <div className="mt-8 flex justify-end gap-3">
        <button
          onClick={handleContinue}
          disabled={testStatus !== "success"}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function FounderProfileStep({
  state,
  onComplete,
  onSaving,
}: {
  state: OnboardingState;
  onComplete: (data?: Record<string, any>) => void;
  onSaving: (saving: boolean) => void;
}) {
  const [riskTolerance, setRiskTolerance] = useState<number>(5);
  const [workingStyle, setWorkingStyle] = useState<"solo" | "team">("solo");
  const [experience, setExperience] = useState<string>("first-time");

  const handleContinue = async () => {
    onSaving(true);
    try {
      onComplete({ riskTolerance, workingStyle, experience });
    } finally {
      onSaving(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Your Founder Profile</h2>
      <p className="text-gray-300 mb-6">
        This helps us customize Mekong to your decision-making style.
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            Risk tolerance (1-10, 1=conservative, 10=aggressive)
          </label>
          <input
            type="range"
            min="1"
            max="10"
            value={riskTolerance}
            onChange={(e) => setRiskTolerance(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-gray-400 mt-1">
            <span>Conservative</span>
            <span className="font-medium text-blue-400">{riskTolerance}</span>
            <span>Aggressive</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Working style</label>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setWorkingStyle("solo")}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                workingStyle === "solo"
                  ? "border-blue-500 bg-blue-900/30"
                  : "border-gray-700 hover:border-gray-600"
              }`}
            >
              <div className="font-medium">Solo Operator</div>
              <div className="text-sm text-gray-400">Prefer to work alone</div>
            </button>
            <button
              type="button"
              onClick={() => setWorkingStyle("team")}
              className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                workingStyle === "team"
                  ? "border-blue-500 bg-blue-900/30"
                  : "border-gray-700 hover:border-gray-600"
              }`}
            >
              <div className="font-medium">Team Builder</div>
              <div className="text-sm text-gray-400">Enjoy collaboration</div>
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Founding experience</label>
          <select
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="first-time">First-time founder</option>
            <option value="experienced">Previously founded a company</option>
            <option value="serial">Serial founder (3+ companies)</option>
          </select>
        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={handleContinue}
          className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
        >
          Continue
        </button>
      </div>
    </div>
  );
}

function TutorialStep({ state, onComplete }: { state: OnboardingState; onComplete: () => void }) {
  const [running, setRunning] = useState(false);
  const [output, setOutput] = useState<string[]>([]);

  const runMission = async () => {
    setRunning(true);
    setOutput([]);

    // Simulate mission execution phases
    const phases = [
      "Planning: Breaking down your goal...",
      "Research: Gathering information...",
      "Analysis: Synthesizing insights...",
      "Verification: Checking quality...",
      "Complete: Your AI team has finished!",
    ];

    for (const phase of phases) {
      await new Promise((resolve) => setTimeout(resolve, 800));
      setOutput((prev) => [...prev, phase]);
    }

    setTimeout(() => {
      setRunning(false);
      onComplete();
    }, 500);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Your First Mission</h2>
      <p className="text-gray-300 mb-6">
        Let's run a simple mission to see Mekong in action. Watch the AI work autonomously.
      </p>

      <div className="mb-6">
        <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
          <div className="font-medium mb-2">Template: Research a topic</div>
          <div className="text-sm text-gray-400">
            Analyze competitor trends in your industry and generate insights.
          </div>
          <div className="text-sm text-gray-400 mt-1">
            Cost: 3 MCU | Time: ~2 minutes
          </div>
        </div>
      </div>

      <button
        onClick={runMission}
        disabled={running}
        className="w-full py-4 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-medium transition-colors mb-4"
      >
        {running ? "Running..." : "▶ Run Mission"}
      </button>

      {output.length > 0 && (
        <div className="bg-black rounded-lg p-4 border border-gray-800 font-mono text-sm">
          <div className="text-gray-400 mb-2">Output:</div>
          {output.map((line, i) => (
            <div key={i} className="text-green-400 mb-1 whitespace-pre-wrap">
              {line}
            </div>
          ))}
        </div>
      )}

      {!running && output.length > 0 && (
        <div className="mt-4 p-4 bg-green-900/30 border border-green-700 rounded-lg">
          <div className="text-green-400 font-medium">✓ Mission complete!</div>
          <div className="text-sm text-gray-300 mt-1">
            Your AI team has successfully completed the research mission. You're ready to start
            building your autonomous business.
          </div>
        </div>
      )}
    </div>
  );
}

function CompletionStep() {
  return (
    <div className="text-center">
      <div className="text-6xl mb-4">🎉</div>
      <h2 className="text-2xl font-bold mb-4">You're All Set!</h2>
      <p className="text-gray-300 mb-8">
        Your first mission completed successfully. You're ready to build your company.
      </p>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 text-left mb-8">
        <h3 className="font-bold mb-4">Next steps:</h3>
        <ul className="space-y-3">
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">→</span>
            <span>
              <strong>Explore commands:</strong> Run{" "}
              <code className="bg-gray-900 px-2 py-1 rounded">mekong help</code> to see all 290+
              commands
            </span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">→</span>
            <span>
              <strong>Run your own mission:</strong>{" "}
              <code className="bg-gray-900 px-2 py-1 rounded">mekong cook "your goal"</code>
            </span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">→</span>
            <span>
              <strong>View dashboard:</strong>{" "}
              <a href="https://ide.mekongmind.com" className="text-blue-400 hover:underline">
                ide.mekongmind.com
              </a>
            </span>
          </li>
          <li className="flex items-start">
            <span className="text-blue-400 mr-2">→</span>
            <span>
              <strong>Join community:</strong> Connect with other founders on Discord
            </span>
          </li>
        </ul>
      </div>

      <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-6">
        <div className="text-blue-400 font-medium mb-2">You have 50 free credits to start</div>
        <p className="text-sm text-gray-300">
          Track your consumption with <code className="bg-gray-900 px-2 py-1 rounded">mekong usage</code>.
          Upgrade when you need more capacity.
        </p>
      </div>
    </div>
  );
}
