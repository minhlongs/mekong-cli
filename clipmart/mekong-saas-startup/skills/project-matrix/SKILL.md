---
name: project-matrix
description: "Show project priority matrix — ranked by business impact (ROI + maturity + activity)"
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---


# /project-matrix — Project Priority Ranking

Shows all projects ranked by business impact score combining ROI, code maturity, and dispatch activity.

## Implementation

```bash
echo "=== PROJECT PRIORITY MATRIX ==="
echo "$(date)"
echo ""

node -e "
  try {
    const pm = require('$HOME/mekong-cli/apps/openclaw-worker/lib/project-priority-matrix');
    const matrix = pm.getProjectMatrix();

    console.log('Rank | Project              | Tier     | State        | Score | Maturity | ROI | Activity');
    console.log('-----|----------------------|----------|--------------|-------|----------|-----|--------');
    matrix.forEach((p, i) => {
      console.log([
        String(i+1).padStart(3) + '.',
        p.name.padEnd(20),
        p.tier.padEnd(8),
        p.state.padEnd(12),
        String(p.total).padStart(5),
        String(p.maturity).padStart(8),
        String(p.roi).padStart(3),
        String(p.activity).padStart(8),
      ].join(' | '));
    });

    console.log('');
    console.log('Score = Maturity(0-40) + ROI(0-30) + Activity(0-30) = max 100');
    console.log('');

    const top = pm.getTopProjects(3);
    console.log('Focus projects: ' + top.map(p => p.name + '(' + p.total + ')').join(', '));
  } catch(e) {
    console.log('Error: ' + e.message);
  }
" 2>/dev/null
```

## Goal context

<goal>$ARGUMENTS</goal>

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
