# Research: Git Staging Risks

## Findings

### Staged Files Analysis (28 modified, 9 untracked)
- **Modified**: Runtime state files (.mekong/, .antigravity/, openclaw-worker/data/), algo-trader refactors, sophia-proposal layout
- **Untracked**: New algo-trader modules (backtest metrics, CLI commands, bot engine types), openclaw google-intel, algo-trader security audit plan

### .gitignore Coverage
- `node_modules/` — covered (line 31)
- `.env`, `.env.local`, `*.env` — covered (lines 27-28, 139-140)
- `dist/` — covered (line 35)
- `.mekong/` — listed in .gitignore (line 82) but files show as modified = **previously tracked**
- `.antigravity/` — NOT in .gitignore → will be committed

### Risk Assessment
- `.mekong/` files: audit.yaml, memory.yaml, schedule.yaml, swarm.yaml, telemetry — previously tracked, gitignore won't help until `git rm --cached`
- No .env files found in untracked
- No API keys detected in diff
- openclaw-worker data files are runtime state (JSON) — acceptable to commit as they track mission history
