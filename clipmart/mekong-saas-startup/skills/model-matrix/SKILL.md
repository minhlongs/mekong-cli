---
name: model-matrix
description: "Show model capabilities matrix — which model for which task type"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /model-matrix — Model Capabilities & Routing

## Implementation

```bash
echo "=== MODEL ROUTING MATRIX ==="
node -e "
  const mr = require('$HOME/mekong-cli/apps/openclaw-worker/lib/model-router');
  const matrix = mr.getModelMatrix();
  console.log('Model             | Tier   | Speed  | Context | Strengths');
  console.log('------------------|--------|--------|---------|----------');
  matrix.forEach(m => {
    console.log(m.model.padEnd(17) + ' | ' + m.tier.padEnd(6) + ' | ' + m.speed.padEnd(6) + ' | ' + m.context.padEnd(7) + ' | ' + m.strengths);
  });
  console.log('');
  const tasks = ['Refactor authentication architecture', '/cook Build landing page', 'Fix lint errors in utils.ts'];
  console.log('--- Sample Routing ---');
  tasks.forEach(t => {
    const r = mr.recommendModel(t);
    console.log('  ' + t.slice(0,40).padEnd(40) + ' -> ' + r.tier + ' (' + r.reason + ')');
  });
" 2>/dev/null
```

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
