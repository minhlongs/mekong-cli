# openclaw-agents

Python agent modules extracted from `apps/openclaw-worker/src/`.

## Modules

| Module | Purpose |
|--------|---------|
| `agent_dispatcher.py` | Hybrid LLM Router — route_and_execute flow |
| `task_classifier.py` | Task complexity/intent classification |
| `model_selector.py` | Model selection based on task type |
| `cost_estimator.py` | Token/cost estimation |
| `fallback_chain.py` | Model fallback chain management |
| `mcu_gate.py` | Mission Control Unit gate logic |

## JS↔Python Contract

Communication between the JS engine (`@mekong/openclaw-engine`) and Python agents uses **subprocess** invocation:

```js
// From JS (Node.js)
const { execSync } = require('child_process');
const result = execSync(
  `python3 packages/openclaw-agents/task_classifier.py --task "${taskContent}"`,
  { encoding: 'utf-8', timeout: 30000 }
);
const classification = JSON.parse(result);
```

### Input/Output Format

- **Input**: CLI args or stdin (JSON)
- **Output**: stdout JSON
- **Errors**: stderr + non-zero exit code

### Example: Task Classification

```bash
python3 packages/openclaw-agents/task_classifier.py --task "Fix build error in auth module"
# Output: {"complexity": "simple", "intent": "FIX", "confidence": 0.95}
```

## Development

```bash
cd packages/openclaw-agents
python3 -m pytest  # when tests exist
```
