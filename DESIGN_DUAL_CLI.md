# Dual CLI Architecture: Mekong (mk) wrapping Agent Kit (ak) on Shared Harness

**Goal**: Mekong CLI (`mk`) hosts the Agent Kit CLI (`ak` / `claude`) on its harness infrastructure — shared hooks, sessions, MCP, agents, skills, memory — not just spawning a subprocess.

---

## Current State Analysis

| Component | Mekong (`mk`) | Agent Kit (`ak` / `claude`) |
|-----------|---------------|-----------------------------|
| Entry point | `scripts/mekong-wrapper.sh` | `claude` binary (Anthropic's) |
| Config root | `~/mekong-cli/.claude/` | `~/.claude/` |
| Commands | `.claude/commands/` (342+) | `.claude/commands/` (~18 claudekit) |
| Skills | `.claude/skills/` (542) | `.claude/skills/` |
| Hooks | `.claude/hooks/` + `mekong/hooks/` | `.claude/hooks/` |
| Agents | `.claude/agents/` + `mekong/agents/` | `.claude/agents/` |
| MCP | `src/core/mcp/` + adapters | `~/.claude/mcp.json` |
| Runtime | Python (PEV engine) + Node (bootstrap) | Node (Claude Code) |

**Current bug**: `mk` just spawns `claude` binary via wrapper → inherits NO Mekong harness (hooks, skills, agents, memory).

---

## Target Architecture: Single Process, Dual Persona

```
┌─────────────────────────────────────────────────────────────────┐
│                        MEKONG HOST PROCESS                      │
│  (Single Python/Node process — the "harness runtime")           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │   MEKONG PERSONA │    │      AGENT KIT PERSONA (ak)      │  │
│  │   (mk commands)  │    │      (claude commands)           │  │
│  ├──────────────────┤    ├──────────────────────────────────┤  │
│  │ cook / fix / plan│    │ plan / cook / fix / review       │  │
│  │ deploy / audit   │    │ scouting / brainstorm / journal  │  │
│  │ strat / finance  │    │ code / test / ship               │  │
│  │ particle / zenos │    │ docs / simplify / preview        │  │
│  └────────┬─────────┘    └──────────────┬───────────────────┘  │
│           │                             │                       │
│           └──────────────┬──────────────┘                       │
│                          ▼                                       │
│         ┌──────────────────────────────────┐                    │
│         │       SHARED HARNESS CORE        │                    │
│         ├──────────────────────────────────┤                    │
│         │  Hook Engine (Pre/Post/Session)  │                    │
│         │  Session Manager (state, memory) │                    │
│         │  Agent Runtime (spawn, comms)    │                    │
│         │  MCP Host (servers + clients)    │                    │
│         │  Skill Loader (542 skills)       │                    │
│         │  Command Router (.claude/commands)│                   │
│         │  Memory Layer (codebase-memory)  │                    │
│         │  Config (.ck.json, settings)     │                    │
│         └──────────────────────────────────┘                    │
│                          │                                       │
│                          ▼                                       │
│         ┌──────────────────────────────────┐                    │
│         │      LLM PROVIDER ABSTRACTION    │                    │
│         │  claude-opus-4-8 / sonnet / qwen │                    │
│         └──────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Phase 1: Harness Core Extraction (Week 1)
Extract the harness runtime from both codebases into a shared library.

**New Structure:**
```
mekong-cli/
├── harness/                          # ← NEW: Shared harness core
│   ├── src/
│   │   ├── core/
│   │   │   ├── hook-engine.ts        # Unified hook system
│   │   │   ├── session-manager.ts    # Session state & memory
│   │   │   ├── agent-runtime.ts      # Subagent spawn/comms
│   │   │   ├── mcp-host.ts           # MCP server/client
│   │   │   ├── skill-loader.ts       # Skill discovery/load
│   │   │   ├── command-router.ts     # /.claude/commands dispatch
│   │   │   ├── memory-layer.ts       # codebase-memory-mcp
│   │   │   └── config-manager.ts     # .ck.json, settings.json
│   │   ├── providers/
│   │   │   ├── llm-router.ts         # 3-var universal endpoint
│   │   │   └── adapters/             # claude, gemini, qwen, local
│   │   └── personas/
│   │       ├── mekong-persona.ts     # mk command set
│   │       └── agentkit-persona.ts   # ak/claude command set
│   ├── package.json                  # harness-core package
│   └── tsconfig.json
├── packages/
│   └── harness-core/                 # Published npm package
├── .claude/                          # ← MERGED: single config root
│   ├── commands/                     # ALL commands (mk + ak)
│   ├── skills/                       # ALL skills
│   ├── agents/                       # ALL agents
│   ├── hooks/                        # ALL hooks (source of truth)
│   ├── settings.json                 # UNIFIED settings
│   └── .ck.json                      # UNIFIED kit config
├── scripts/
│   ├── mk                            # Entry: loads harness + mekong persona
│   └── ak                            # Entry: loads harness + agentkit persona
```

### Phase 2: Single Config Root Merge (Week 1-2)

**Merge Strategy:**
```
~/.claude/                 ← Agent Kit global (user-level)
~/mekong-cli/.claude/      ← Mekong project-level (repo-specific)

→ UNIFY TO:
~/mekong-cli/.claude/      ← Single source of truth for BOTH personas
    settings.json          ← Merged: hooks + permissions + MCP + env
    .ck.json               ← Merged: kit config + model overrides
    commands/              ← 342+ mk + 18 ak = ~360 commands
    skills/                ← 542 skills (shared)
    agents/                ← 14 stock + 6 mekong = 20 agents
    hooks/                 ← Source of truth (symlinked to ~/.claude/hooks/)
```

**Symlink Strategy:**
```bash
# ~/.zshrc or shell-init.sh
ln -sfn ~/mekong-cli/.claude/hooks ~/.claude/hooks
ln -sfn ~/mekong-cli/.claude/commands ~/.mekong-commands  # optional alias
```

### Phase 3: Entry Points (Week 2)

**`scripts/mk`** — Mekong persona entry:
```bash
#!/usr/bin/env node
// Load harness core
const { Harness } = require('@mekong/harness-core');
const { MekongPersona } = require('@mekong/harness-core/personas/mekong-persona');

const harness = new Harness({
  configRoot: process.env.MEKONG_ROOT || '~/mekong-cli',
  persona: new MekongPersona(),
  model: process.env.MEKONG_MODEL || 'claude-opus-4-8',
});

harness.run(process.argv.slice(2));
```

**`scripts/ak`** — Agent Kit persona entry:
```bash
#!/usr/bin/env node
const { Harness } = require('@mekong/harness-core');
const { AgentKitPersona } = require('@mekong/harness-core/personas/agentkit-persona');

const harness = new Harness({
  configRoot: process.env.MEKONG_ROOT || '~/mekong-cli',
  persona: new AgentKitPersona(),
  model: process.env.AK_MODEL || 'claude-opus-4-8',
});

harness.run(process.argv.slice(2));
```

### Phase 4: Command Router Unification (Week 2-3)

**Router loads ALL commands, dispatches by persona prefix:**

```typescript
// harness/src/core/command-router.ts
class CommandRouter {
  private commands: Map<string, CommandDef> = new Map();
  private personaPrefixes = {
    mekong: ['mekong:', 'mk:', 'strategy:', 'finance:', 'particle:', 'studio:'],
    agentkit: ['plan', 'cook', 'fix', 'review', 'scout', 'brainstorm', 'code', 'test', 'ship'],
  };

  loadCommands(configRoot: string) {
    // Load from .claude/commands/*.md
    // Tag each with persona affinity
  }

  route(input: string, persona: Persona): CommandDef | null {
    // If input matches persona prefix → allow
    // If input is neutral (help, status) → allow both
    // If input matches OTHER persona → suggest switch
  }
}
```

**Persona-aware command execution:**
```bash
# In mk persona:
mk plan "new feature"     # → routes to mk plan command
/mk:plan "new feature"   # → explicit mk prefix
/ak:plan "new feature"   # → explicit ak prefix (switch persona)

# In ak persona:
/plan "new feature"      # → routes to ak plan command
/mk:strategy analyze     # → switch to mk for strategy
```

### Phase 5: Hook Engine Unification (Week 3)

**Single hook engine processes ALL events for BOTH personas:**

```typescript
// harness/src/core/hook-engine.ts
class HookEngine {
  private hooks: Hook[] = [];

  async loadFromConfigRoot(configRoot: string) {
    // Load from .claude/hooks/*.cjs
    // Load from .claude/settings.json hooks[]
    // Apply to BOTH personas
  }

  async fire(event: HookEvent, context: HarnessContext) {
    // Context includes persona for conditional hooks
    const relevantHooks = this.hooks.filter(h => 
      h.match(event) && (!h.persona || h.persona === context.persona)
    );
    await Promise.all(relevantHooks.map(h => h.execute(context)));
  }
}
```

**Hook config in settings.json:**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Write",
        "command": "~/.claude/hooks/cbm-code-discovery-gate",
        "persona": "both"
      },
      {
        "matcher": "Agent|Task",
        "command": "~/.claude/hooks/subagent-init.cjs",
        "persona": "agentkit"
      },
      {
        "matcher": "mekong:*",
        "command": "~/.claude/hooks/mekong-pre-tool.cjs",
        "persona": "mekong"
      }
    ]
  }
}
```

### Phase 6: Session & Memory Unification (Week 3-4)

**Single session manager, dual persona state:**

```typescript
// harness/src/core/session-manager.ts
interface SessionState {
  id: string;
  persona: 'mekong' | 'agentkit';
  history: Message[];
  memory: {
    codebase: CodebaseMemory;
    project: ProjectMemory;
    user: UserPreferences;
  };
  workingDir: string;
  spawnedAgents: AgentInvocation[];
}

class SessionManager {
  // Shared across personas — switch persona mid-session
  async switchPersona(sessionId: string, newPersona: Persona) {
    // Preserve history, memory, working dir
    // Only swap command router + model config
  }
}
```

---

## Migration Path (Non-Breaking)

### Step 1: Create harness-core package (Week 1)
```bash
cd ~/mekong-cli
mkdir -p harness/src/{core,providers,personas}
# Extract shared code from:
# - .claude/hooks/*.cjs → harness/src/core/hook-engine.ts
# - scripts/mekong-wrapper.sh logic → harness/src/core/
# - src/core/llm_client.py → harness/src/providers/llm-router.ts
# - .claude/scripts/*.cjs → harness/src/core/
```

### Step 2: Publish harness-core
```json
// harness/package.json
{
  "name": "@mekong/harness-core",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "bin": {
    "mk": "bin/mk.js",
    "ak": "bin/ak.js"
  }
}
```

### Step 3: Update shell-init.sh
```bash
# shell-init.sh (NEW)
export MEKONG_ROOT="$HOME/mekong-cli"
export PATH="$MEKONG_ROOT/harness/bin:$PATH"

# Alias for muscle memory
alias mk='ush harness/bin/mk'
alias ak='ush harness/bin/ak'
alias mekong='mk'  # backward compat
alias mekong-claude='ak'  # backward compat
```

### Step 4: Deprecate old wrapper
```bash
# scripts/mekong-wrapper.sh → DEPRECATED
# Keep for 30 days with warning:
echo "⚠️  mekong-wrapper.sh deprecated. Use 'mk' or 'ak' instead."
exec mk "$@"
```

---

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| **Single process, dual persona** | Avoids IPC overhead, shared memory, unified hooks |
| **TypeScript harness core** | Type safety, shared with Node-based Claude Code |
| **Python PEV engine as subprocess** | Keep existing orchestrator, spawn via harness |
| **Merged .claude/ root** | Single config source, no sync issues |
| **Persona-aware command router** | Clean UX: `/mk:*` vs `/ak:*` vs neutral |
| **Settings.json as hook source** | Claude Code compatible, declarative |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing `mekong` commands | Deprecation period, alias shims, automated tests |
| Hook conflicts between personas | Persona-scoped hooks in settings.json |
| Memory bloat from dual agent runs | Session isolation, configurable context limits |
| MCP server conflicts | Harness manages single MCP host, multiplexes |

---

## Success Criteria

- [ ] `mk` and `ak` share **same process** (verify with `ps aux`)
- [ ] Hooks fire for **both** personas from single `.claude/hooks/`
- [ ] Skills load **once**, available to both personas
- [ ] MCP servers start **once**, shared
- [ ] `mk plan` → uses Mekong planner; `ak plan` → uses Agent Kit planner
- [ ] `/mk:cook` in `ak` session switches persona seamlessly
- [ ] Session state persists across persona switches
- [ ] Zero breaking changes for existing `mekong` users (30-day deprecation)

---

## Next Steps

1. **Approve architecture** → Proceed to Phase 1 implementation
2. **Create harness-core package** with TypeScript
3. **Extract hook engine** from `.claude/hooks/*.cjs`
4. **Merge `.claude/` configs** with migration script
5. **Build `mk` and `ak` entry points** using harness-core
6. **Integration test** with both command sets

---

*This design makes Mekong the **infrastructure platform** and Agent Kit a **persona** on that platform — exactly as requested.*