# @agencyos/vibe-analytics

The analytics engine for the Vibe ecosystem, providing Growth Telemetry and Engineering Metrics.

## Features

### 🛠️ DevOps & Engineering Metrics (DORA)
Calculate industry-standard engineering metrics directly from your GitHub repository using the GraphQL API.

**DORA Metrics:**
- **Deployment Frequency:** How often code is released.
- **Lead Time for Changes:** Time from commit to merge/release.
- **Change Failure Rate:** Percentage of releases requiring hotfixes.
- **Time to Restore:** (Placeholder) Time to recover from incidents.

**Engineering Velocity:**
- **Cycle Time:** Total time from first commit to PR merge.
- **PR Pickup Time:** Time from PR creation to first review.
- **PR Review Time:** Time from first review to merge.
- **PR Size:** Lines of code changed (additions + deletions).

### 📈 Growth Telemetry
(Existing functionality for tracking growth metrics)

## CLI Usage

The metrics engine is integrated into the `vibe` CLI:

```bash
# Analyze the current repository (auto-detected)
vibe metrics

# Analyze a specific repository
vibe metrics --owner facebook --repo react

# Specify analysis period (default 30 days)
vibe metrics --days 90

# Output as JSON (useful for piping to other tools)
vibe metrics --json
```

## Requirements

You must set the `GITHUB_TOKEN` environment variable to a valid GitHub Personal Access Token with `repo` read permissions.

```bash
export GITHUB_TOKEN=your_github_token
```

## Installation

```bash
npm install @agencyos/vibe-analytics
```

## API Usage

You can also use the metrics engine programmatically:

```typescript
import { GitHubClient, MetricsEngine } from '@agencyos/vibe-analytics';

const client = new GitHubClient(process.env.GITHUB_TOKEN);
const engine = new MetricsEngine();

const data = await client.fetchRepoData('owner', 'repo', 30);
const report = engine.calculate(data, 30);

console.log(report.dora.deploymentFrequency);
```
