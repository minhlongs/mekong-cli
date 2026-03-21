---
description: "Show algorithm health — coverage, test status, lines per project"
argument-hint: [--all | --project=sophia-proposal]
allowed-tools: Bash
---

# /algo-status — Algorithm Health Dashboard

Shows algorithm modules across all projects: coverage, test status, LOC.

## Implementation

```bash
echo "=== ALGORITHM STATUS ==="
echo "$(date)"
echo ""

node -e "
  const ao = require('$HOME/mekong-cli/apps/openclaw-worker/lib/algo-orchestrator');
  const results = ao.scanAllProjects();

  for (const [project, data] of Object.entries(results)) {
    if (data.total === 0) {
      console.log(project + ': no algorithms');
      continue;
    }
    console.log(project + ': ' + data.total + ' algorithms, ' + data.totalLines + ' lines, ' + data.withTests + '/' + data.total + ' tested');
    console.log('  Name                  | Lines | Exports | Test');
    console.log('  ----------------------|-------|---------|-----');
    for (const a of data.algorithms) {
      console.log('  ' + a.name.padEnd(22) + '| ' + String(a.lines).padStart(5) + ' | ' + String(a.exports).padStart(7) + ' | ' + (a.hasTest ? 'YES' : 'NO'));
    }
    console.log('  Score: ' + ao.getAlgoScore('apps/' + project) + '/20');
    console.log('');
  }
" 2>/dev/null
```

## Goal context

<goal>$ARGUMENTS</goal>
