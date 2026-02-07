# 🧬 Core Foundation Layer

> **Quintessence absorbed from Sophia AI Factory** - The DNA of Mekong CLI

---

## 📦 Packages

### @mekong/vibe
**🌐 Unified VIBE Ecosystem - Core Foundation**

The heart of the Mekong CLI framework. Provides core primitives for building AI-powered workflows:
- Flow builder & execution engine
- Hardened production patterns (error boundaries, diagnostics, deployment)
- Project scaffolding & type system
- Planet architecture foundation

**Origin:** `apps/sophia-ai-factory/packages/vibe`
**Status:** ✅ Migrated (Phase 1)

### @mekong/vibe-agents
**🟣 Saturn - AI Agent Orchestration Layer**

Orchestration primitives for multi-agent systems:
- Agent registry & lifecycle management
- Task delegation & coordination
- LLM integration (Gemini, Claude)
- Testing infrastructure (vitest)

**Origin:** `apps/sophia-ai-factory/packages/vibe-agents`
**Status:** ✅ Migrated (Phase 1)

### @mekong/shared
**🔧 Shared Utilities**

Cross-package utilities and shared types:
- Logger
- Common type definitions
- Utility functions

**Origin:** `apps/sophia-ai-factory/packages/shared`
**Status:** ✅ Migrated (Phase 1)

---

## 🏗️ Architecture

```
packages/core/
├── vibe/           # Foundation layer (flow, hardened, types)
├── vibe-agents/    # Orchestration layer (agent registry)
└── shared/         # Utilities (logger, types)
```

**Dependency Flow:**
```
vibe → shared
vibe-agents → (standalone, uses @google/generative-ai)
```

---

## 📝 Migration Log

**Phase 1: Absorb Quintessence** (2026-02-07)
- Copied from `apps/sophia-ai-factory/packages/`
- Renamed namespace: `@agencyos/*` → `@mekong/*`
- Updated internal imports
- Removed planet dependencies from vibe (now core-only)

---

## 🚀 Usage

```typescript
// Core VIBE primitives
import { VIBEProject, VIBEFlow } from '@mekong/vibe';

// Agent orchestration
import { AgentRegistry } from '@mekong/vibe-agents';

// Shared utilities
import { logger } from '@mekong/shared';
```

---

## 🧪 Testing

```bash
# Test all core packages
cd packages/core/vibe-agents
npm test

# Build verification
npm run build
```

---

## 🎯 Next Steps

- **Phase 2:** Migrate integrations layer (bridge, CRM)
- **Phase 3:** Migrate tooling layer (dev, analytics)
- **Phase 4:** Migrate business layer (money, ops, marketing)
- **Phase 5:** Migrate UI layer (vibe-ui, i18n)

---

_Part of the Mekong CLI Hub Transformation Plan_
