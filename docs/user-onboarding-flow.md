# User Onboarding Flow Design

**Status:** Draft  
**Created:** 2026-06-20  
**Author:** Claude Opus 4.8  
**Related:** Task #95, #205, #213, #218

---

## Overview

The Mekong IDE onboarding flow guides users from first visit to their first successful autonomous mission. The design addresses three primary user personas:

1. **CLI-First Developer** - Terminal-oriented, wants to get started quickly with commands
2. **Dashboard-First Business User** - Prefers visual interface, guided wizards
3. **Vietnamese Market User** - Zalo integration, local payment methods, Vietnamese UI

### Design Goals

- **Time to First Value (TTFV):** < 10 minutes from signup to first completed mission
- **Progressive Disclosure:** Introduce complex concepts (10 layers, PEV, Constitutional AI) gradually
- **Save & Resume:** Users can pause and resume at any step
- **Multiple Entry Points:** CLI wizard, dashboard flow, or landing page CTA
- **CLI + Dashboard Sync:** State shared between both interfaces

---

## User Journey Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER JOURNEY MAP                          │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│   Stage     │   Goal       │   Duration  │   Channels  │  Success│
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ 1. Discovery│ Understand   │   < 2 min   │  Landing    │ Landing│
│             │ value prop   │             │  page, docs │ page   │
│             │             │             │  view       │  view  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ 2. Signup   │ Create       │   < 3 min   │  Web,      │ Account│
│             │ account      │             │  Zalo OA   │ created│
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ 3. Setup    │ Configure    │   < 5 min   │  Dashboard │ LLM +  │
│ Wizard      │ LLM +        │             │  wizard    │ Profile│
│             │ Profile      │             │             │ config │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ 4. First    │ Get a       │   < 10 min  │  CLI/API    │ Mission│
│ Mission     │ quick win   │             │  or dashboard│ done  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────┤
│ 5. Explore  │ Discover     │   Ongoing  │  Dashboard │ 3+     │
│             │ commands     │             │  discovery │ missions│
│             │              │             │             │ run    │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

---

## Flow 1: Dashboard-First Onboarding (Primary)

### Entry Point: `/onboarding` (dashboard route)

```
GET /onboarding → Check auth status
  ├─ Not authenticated → Landing page with Sign Up / Log In
  └─ Authenticated, not onboarded → Setup wizard step 1
```

### Step-by-Step Flow

#### Step 1: Welcome & Vision (2 min)

**Screen:** Welcome to Mekong IDE

**Content:**
```
┌─────────────────────────────────────────────────────────┐
│  🌟 Welcome to Mekong IDE                                │
│                                                          │
│  You're about to build your one-person company.         │
│  10 business layers. Zero employees. Full autonomy.     │
│                                                          │
│  First, tell us about your vision:                       │
│                                                          │
│  [What kind of business are you building?]              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ SaaS product • E-commerce • Agency • Consulting    │ │
│  │ Creator • Trading • Manufacturing • Other          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Your primary goal for the next 90 days]              │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Launch MVP • Get first customers • Automate ops    │ │
│  │ Build team • Scale revenue • Explore ideas         │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│          [Skip for now →]         [Continue →]         │
└─────────────────────────────────────────────────────────┘
```

**Data stored:** `user_profile.business_type`, `user_profile.ninety_day_goal`

---

#### Step 2: LLM Provider Configuration (3 min)

**Screen:** Connect Your AI Brain

**Content:**
```
┌─────────────────────────────────────────────────────────┐
│  🤖 Connect Your AI Provider                             │
│                                                          │
│  Mekong works with any OpenAI-compatible API.           │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Provider:                                           │ │
│  │ ● Anthropic Claude    ○ OpenAI GPT                 │ │
│  │ ○ OpenRouter          ○ DeepSeek                   │ │
│  │ ○ Local (Ollama)      ○ Google Gemini              │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  API Key:                                               │
│  ┌────────────────────────────────────────────────────┐ │
│  │ sk-ant-...                                          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Model:                                                 │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Claude Sonnet 4 (recommended)                     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Test Connection] [Validate]                          │
│                                                          │
│  💡 Need help? Visit our LLM setup guide.               │
│                                                          │
│          ← Back              [Continue →]              │
└─────────────────────────────────────────────────────────┘
```

**Validation:** Test API call to provider  
**Data stored:** `llm_config.provider`, `llm_config.api_key_encrypted`, `llm_config.model`

**For VN Users:** Show Zalo OA option for LLM credits purchase

---

#### Step 3: Founder Genome Profiling (5 min)

**Screen:** Your Founder Profile

**Content:**
```
┌─────────────────────────────────────────────────────────┐
│  🧬 Founder Genome Profiling                            │
│                                                          │
│  This helps us customize Mekong to your style.          │
│  All data stays encrypted on your device.               │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ How do you make decisions?                        │ │
│  │                                                    │ │
│  │   Data-driven   ───────●────   Gut instinct      │ │
│  │                                                    │ │
│  │   Fast           ──────●────   Thorough          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ What's your risk tolerance?                       │ │
│  │                                                    │ │
│  │   Conservative  ─────●────   Aggressive          │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Your working style:                               │ │
│  │                                                    │ │
│  │   Solo operator  ○  Team builder                  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  [Additional: industry, experience, goals...]          │
│                                                          │
│          ← Back              [Complete Setup →]        │
└─────────────────────────────────────────────────────────┘
```

**Data stored:** `founder_genome` (encrypted locally)  
**Result:** 10 trait scores + cluster classification

---

#### Step 4: Quick Win Tutorial (5 min)

**Screen:** Your First Autonomous Mission

**Content:**
```
┌─────────────────────────────────────────────────────────┐
│  🚀 Your First Mission                                   │
│                                                          │
│  Let's run a simple mission to see Mekong in action.    │
│                                                          │
│  Pick a template:                                        │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📋 Research a topic                               │  │
│  │ "Analyze competitor trends in [your industry]"    │  │
│  │                                                    │  │
│  │ ⏱️  ~2 minutes   💰 3 MCU                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📝 Draft a blog post                             │  │
│  │ "Write a 500-word introduction to your business" │  │
│  │                                                    │  │
│  │ ⏱️  ~3 minutes   💰 5 MCU                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 💡 Create a business plan                        │  │
│  │ "Draft a one-page business plan"                 │  │
│  │                                                    │  │
│  │ ⏱️  ~5 minutes   💰 10 MCU                       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Or enter custom prompt:                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│          ← Back              [Run Mission →]           │
└─────────────────────────────────────────────────────────┘
```

**Background:** PEV engine executes the mission  
**Display:** Real-time streaming output showing Plan → Execute → Verify

---

#### Step 5: Onboarding Complete!

**Screen:** You're Ready to Build Your Company

**Content:**
```
┌─────────────────────────────────────────────────────────┐
│  🎉 You're All Set!                                       │
│                                                          │
│  Your first mission completed successfully!             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  💳 Credits: 190 remaining                       │  │
│  │  📊 Usage: 10 MCU consumed                       │  │
│  │  ⏱️  Time saved: ~2 hours                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  Next steps:                                             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 🎯 Explore Commands                             │ │
│  │ Discover 443 commands across 10 business layers │ │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 📖 Read the Guide                               │ │
│  │ Learn PEV orchestration and Constitutional AI   │ │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 💬 Join Community                              │ │
│  │ Connect with other solo founders                │ │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│          [Go to Dashboard]     [Run Another Mission]   │
└─────────────────────────────────────────────────────────┘
```

---

## Flow 2: CLI-First Onboarding (Alternative)

### Entry Point: `mekong onboard` or first `mekong` run

```
$ mekong
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ╔═══════════════════════════════════════════════════════╗ │
│  ║   Welcome to Mekong CLI — Your AI Business Platform  ║ │
│  ╚═══════════════════════════════════════════════════════╝ │
│                                                             │
│  Before you can run missions, let's configure Mekong.      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ [1] Configure LLM Provider (required)               │ │
│  │ [2] Set Up Founder Profile (recommended)            │ │
│  │ [3] Quick Tutorial (recommended)                    │ │
│  │ [4] Skip — I know what I'm doing                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  Selection: [1]                                            │
└─────────────────────────────────────────────────────────────┘
```

### Step 1: LLM Configuration (CLI)

```bash
$ mekong onboard llm

=== LLM Provider Setup ===

Select provider:
  [1] Anthropic Claude (recommended)
  [2] OpenAI GPT
  [3] OpenRouter
  [4] Ollama (local)
  [5] Custom endpoint

Your choice: 1

API Key: •••••••••••••••••••••••••••••••••••••[hidden]
Model: claude-sonnet-4 (default) [press Enter or customize]

Testing connection... ✓ Connected!
Rate limit: 1500 requests/min

Configuration saved to ~/.mekong/config.yaml
```

### Step 2: Founder Profile (CLI)

```bash
$ mekong onboard profile

=== Founder Genome ===

Your decision-making style (1-10, 1=data-driven, 10=instinct):
> 6

Risk tolerance (1-10, 1=conservative, 10=aggressive):
> 7

Working preference:
  [1] Solo operator
  [2] Team builder
> 1

Business type:
  [1] SaaS
  [2] E-commerce
  [3] Agency
  [4] Consulting
  [5] Creator
  [6] Other
> 1

Profile encrypted and saved.
```

### Step 3: Tutorial (CLI)

```bash
$ mekong onboard tutorial

=== Quick Tutorial ===

Running a sample research mission...

PEV PLAN:
  Steps: 1. Search web 2. Synthesize findings 3. Generate report

Executing...
[███████████████████████------------------] 60%

Mission complete! (2m 34s)

Next: Try `mekong cook "your own goal"` to start building.
```

---

## Flow 3: Vietnamese Market (VN Pilot)

### Special Considerations

1. **Zalo OA Integration** - Authentication & notifications via Zalo
2. **VietQR Payment** - Bank transfer onboarding
3. **Localized UI** - Vietnamese language option
4. **Pilot Program** - 50 free credits + Zalo welcome call

### VN Onboarding Flow

```
1. Landing (vi.mekongmind.com) → "Dùng thử miễn phí"
2. Zalo OA Auth → "Đăng nhập bằng Zalo"
3. Profile form (Vietnamese) → Tên, Zalo, Loại hình kinh doanh
4. VietQR payment (optional) → 199K → 200 credits
5. Zalo welcome message → "+848xxx" calls within 5 minutes
6. Dashboard tour (Vietnamese)
```

**API:** `POST /v1/pilot/signup` with VN-specific fields  
**Webhook:** Founder notified, Zalo OA sends welcome

---

## Technical Implementation

### Database Schema

```sql
-- User onboarding state
CREATE TABLE user_onboarding (
    user_id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    stage VARCHAR(50) NOT NULL DEFAULT 'landing',
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Profile data
    business_type VARCHAR(100),
    ninety_day_goal VARCHAR(500),

    -- LLM config
    llm_provider VARCHAR(50),
    llm_model VARCHAR(100),
    api_key_encrypted TEXT,

    -- Founder genome (encrypted)
    founder_genome_json JSONB,

    -- Metadata
    source VARCHAR(100),  -- landing_page, cli, referral
    locale VARCHAR(10) DEFAULT 'en'
);

-- Onboarding progress tracking
CREATE TABLE onboarding_events (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_onboarding_user_id ON user_onboarding(user_id);
CREATE INDEX idx_onboarding_stage ON user_onboarding(stage);
CREATE INDEX idx_events_user_id ON onboarding_events(user_id);
CREATE INDEX idx_events_created ON onboarding_events(created_at);
```

### API Routes

```python
# src/api/onboarding_routes.py

@router.post("/onboarding/start")
async def start_onboarding(user: User = Depends(current_user)):
    """Initialize onboarding for new user."""
    pass

@router.post("/onboarding/step")
async def complete_step(
    step_data: OnboardingStepRequest,
    user: User = Depends(current_user)
):
    """Record completion of an onboarding step."""
    pass

@router.get("/onboarding/status")
async def get_status(user: User = Depends(current_user)):
    """Get current onboarding progress."""
    pass

@router.post("/onboarding/llm-config")
async def configure_llm(
    config: LLMConfigRequest,
    user: User = Depends(current_user)
):
    """Save LLM provider configuration."""
    pass

@router.post("/onboarding/founder-profile")
async def save_founder_profile(
    profile: FounderProfileRequest,
    user: User = Depends(current_user)
):
    """Save encrypted founder genome."""
    pass
```

### CLI Integration

```python
# cli/onboarding/__init__.py

class OnboardingWizard:
    """Interactive CLI onboarding wizard."""

    def run(self):
        """Run the full wizard or resume from saved progress."""
        stage = self._load_stage()

        if stage == "complete":
            self._show_already_done()
            return

        steps = {
            "llm": self._step_llm_config,
            "profile": self._step_founder_profile,
            "tutorial": self._step_tutorial,
        }

        for step_name, step_fn in steps.items():
            if stage == step_name or self._should_run(step_name):
                if not step_fn():
                    break  # User exited
                self._save_stage(step_name)

        self._mark_complete()
```

---

## Dashboard Components

### Onboarding Layout (`/onboarding`)

```tsx
// apps/dashboard/app/onboarding/layout.tsx
export default function OnboardingLayout({
  children,
  params: { step }
}: {
  children: ReactNode;
  params: { step: string };
}) {
  const { data: progress } = useOnboardingProgress();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 to-indigo-950">
      {/* Progress indicator */}
      <OnboardingProgressBar currentStep={step} steps={ONBOARDING_STEPS} />

      {/* Step content */}
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>

      {/* Navigation */}
      <OnboardingNav
        onBack={step > 1 ? goBack : null}
        canSkip={canSkipStep(step)}
      />
    </div>
  );
}
```

### Progress Persistence

```typescript
// lib/onboarding/use-onboarding-progress.ts
export function useOnboardingProgress() {
  const { data, mutate } = useSWR<OnboardingProgress>(
    "/api/onboarding/status",
    fetcher,
    {
      refreshInterval: 5000,
    }
  );

  const completeStep = async (step: string, data: any) => {
    await fetch("/api/onboarding/step", {
      method: "POST",
      body: JSON.stringify({ step, data }),
    });
    mutate();
  };

  return { data, completeStep };
}
```

---

## State Management

### User State Schema

```typescript
interface UserOnboardingState {
  userId: string;
  stage: OnboardingStage;
  completedAt?: string;
  profile: {
    businessType?: string;
    ninetyDayGoal?: string;
    industry?: string;
    location?: string;
  };
  llmConfig: {
    provider: LLMProvider;
    apiKeyEncrypted: string;
    model: string;
    isValid: boolean;
  };
  founderGenome?: FounderGenome;
  metrics: {
    timeSpentMinutes: number;
    stepsCompleted: number;
    missionsRun: number;
  };
}

enum OnboardingStage {
  LANDING = "landing",
  SIGNUP = "signup",
  WELCOME = "welcome",
  LLM_CONFIG = "llm_config",
  FOUNDER_PROFILE = "founder_profile",
  TUTORIAL = "tutorial",
  COMPLETE = "complete",
}
```

### Local Storage Fallback

For users without account (guest mode), store state in localStorage:

```typescript
const ONBOARDING_STORAGE_KEY = "mekong_onboarding_state";

function saveOnboardingState(state: UserOnboardingState) {
  if (typeof window !== "undefined") {
    const encrypted = encryptForClient(state);
    localStorage.setItem(ONBOARDING_STORAGE_KEY, encrypted);
  }
}
```

---

## Accessibility & Internationalization

### i18n Keys

```json
{
  "onboarding.welcome.title": "Welcome to Mekong IDE",
  "onboarding.welcome.subtitle": "Build your one-person company with AI",
  "onboarding.llm.label_provider": "AI Provider",
  "onboarding.profile.label_risk": "Risk tolerance",
  "onboarding.tutorial.run": "Run mission",
  "onboarding.complete.title": "You're all set!"
}
```

### Accessibility Requirements

- All interactive elements keyboard navigable
- ARIA labels for screen readers
- High contrast mode support
- Focus management between steps
- Skip to content link

---

## Error Handling & Edge Cases

### Connection Failures

If LLM API test fails:
1. Show clear error message
2. Provide troubleshooting tips
3. Allow "configure later" option
4. Save encrypted key for retry

### Session Timeout

If user leaves mid-onboarding:
- Save progress to localStorage + server
- Resume on next visit to `/onboarding`
- Prompt: "Welcome back! Continue where you left off?"

### Validation

Each step validates before allowing next:
- LLM: Connection test required
- Profile: Minimum fields required
- Tutorial: Mission must complete successfully

---

## Analytics & Metrics

Track these events:

```typescript
const ONBOARDING_EVENTS = {
  // Funnel
  ONBOARDING_START: "onboarding_start",
  STEP_COMPLETE: "onboarding_step_complete",
  STEP_SKIP: "onboarding_step_skip",
  ONBOARDING_COMPLETE: "onboarding_complete",
  ONBOARDING_DROP: "onboarding_drop",

  // Actions
  LLM_CONFIG_SAVE: "llm_config_save",
  LLM_CONFIG_TEST: "llm_config_test",
  PROFILE_SAVE: "profile_save",
  MISSION_RUN: "mission_first_run",

  // Errors
  LLM_CONNECTION_FAIL: "llm_connection_fail",
  MISSION_FAIL: "mission_first_fail",
} as const;
```

---

## Wireframes

See accompanying `.pen` file for interactive wireframes:
- `onboarding-flow-wireframes.pen`

Screens included:
1. Landing page
2. Welcome step
3. LLM configuration
4. Founder profile
5. Tutorial mission
6. Completion screen

---

## Implementation Phases

### Phase 1: Core Dashboard Flow (Week 1-2)
- [ ] Create `/onboarding` route and layout
- [ ] Implement steps 1-3 (Welcome, LLM, Profile)
- [ ] API routes for state persistence
- [ ] Basic progress tracking

### Phase 2: Tutorial Integration (Week 3)
- [ ] Integrate PEV engine for tutorial missions
- [ ] Real-time streaming output
- [ ] Mission templates

### Phase 3: CLI Onboarding (Week 4)
- [ ] `mekong onboard` command
- [ ] Interactive CLI wizard
- [ ] State sync with dashboard

### Phase 4: Vietnamese Market (Week 5-6)
- [ ] VN-specific localization
- [ ] Zalo OA integration
- [ ] VietQR payment flow

### Phase 5: Polish & Analytics (Week 7)
- [ ] A/B test variants
- [ ] Analytics instrumentation
- [ ] Accessibility audit

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Onboarding completion rate | > 70% | Funnel analytics |
| Time to first mission | < 10 min | Event timing |
| 7-day retention | > 50% | Cohort analysis |
| CLI vs Dashboard split | Document | Channel tracking |
| VN conversion rate | > 40% | Regional analytics |

---

## Open Questions

1. Should we offer "guest mode" without account creation?
2. What's the optimal number of profile questions?
3. Should we integrate with social login (Google, GitHub)?
4. How to handle LLM API key security (client-side vs server-side)?
5. Should we provide pre-filled example prompts for tutorial?

---

## References

- [Autonomous Goal Engine (PEV)](./autonomous-goal-engine.md)
- [Founder Genome](./founder-genome.md)
- [Constitutional AI](./constitutional-ai.md)
- [API Documentation Standards](./api/README.md)
