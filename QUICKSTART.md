# Quickstart

Get running in under 5 minutes.

## Option A: Full Platform (clone)

```bash
git clone --depth 1 https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli
source scripts/shell-init.sh    # Adds 'mekong' aliases to your shell
```

Configure your LLM (pick one):

```bash
# OpenRouter (easiest, $5 free credit on signup)
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4

# Or: Ollama (free, runs locally)
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
```

Run your first command:

```bash
mekong cook "Create a Python REST API with FastAPI"
```

## Option B: SDK Only (npm)

```bash
npm install @mekongcli/openclaw-engine
```

```typescript
import { OpenClawEngine } from '@mekongcli/openclaw-engine';

const engine = new OpenClawEngine();
const complexity = engine.classifyComplexity("Deploy microservice");
const result = await engine.submitMission({
  goal: "Create user auth system",
  layer: "engineering",
});
```

## Verify Setup

```bash
# Check mekong is available
mekong status

# Run tests (optional)
cd packages/mekong-cli-core && pnpm test   # 1,263 TS tests
python3 -m pytest tests/ -q                 # 4,450 Python tests
```

## Next Steps

- Run `mekong help` to see all 300+ commands
- Try `mekong plan "your feature idea"` to generate an implementation plan
- Try `mekong founder:validate "your business idea"` for PMF analysis
- See [README.md](README.md) for full documentation
