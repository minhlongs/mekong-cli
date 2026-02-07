# Vibe Analytics Architecture Design

## 1. Overview
`vibe-analytics` is a CLI tool designed to measure software delivery performance using DORA metrics and other key engineering indicators. It integrates with GitHub to fetch data, processes it locally, and provides insights via CLI reports. It is built to be compatible with and potentially extend the existing `vibe-dev` ecosystem.

## 2. Core Metrics

We will focus on the **Four Keys (DORA Metrics)** plus **Cycle Time**:

1.  **Deployment Frequency**: Frequency of successful deployments to production.
    *   *Source*: GitHub Releases or Tags matching a pattern (e.g., `v*`).
2.  **Lead Time for Changes**: The amount of time it takes a commit to get into production.
    *   *Calculation*: `Deployment Time` - `Commit Time` (average).
3.  **Change Failure Rate**: The percentage of deployments causing a failure in production.
    *   *Source*: Deployments followed by a "hotfix" or "rollback" or an issue labeled "incident".
4.  **Time to Restore Service (MTTR)**: How long it takes to recover from a failure.
    *   *Calculation*: Time from "incident" creation to "incident" closure (or hotfix merge).
5.  **Cycle Time**: Time from first commit to PR merge.
    *   *Source*: PRs (merged). `PR Merged At` - `First Commit At`.

## 3. Data Retrieval Strategy

We will reuse the `GitHubClient` from `vibe-dev/src/lib/github-client.ts`.

### GraphQL Queries

**Query 1: Fetch Pull Requests (for Cycle Time & Lead Time)**
```graphql
query GetPullRequests($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, states: MERGED, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        createdAt
        mergedAt
        additions
        deletions
        commits(first: 1) {
          nodes {
            commit {
              committedDate
            }
          }
        }
      }
    }
  }
}
```

**Query 2: Fetch Releases/Tags (for Deployment Frequency)**
```graphql
query GetReleases($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    releases(first: 100, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        tagName
        publishedAt
        isPrerelease
      }
    }
  }
}
```

**Query 3: Fetch Incidents (for Change Failure Rate & MTTR)**
*Assumption*: Incidents are tracked as Issues with a specific label (e.g., "incident", "bug").
```graphql
query GetIncidents($owner: String!, $repo: String!, $label: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, labels: [$label], after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        createdAt
        closedAt
      }
    }
  }
}
```

## 4. Local Storage Schema

We will use a JSON-based storage compatible with `vibe-dev`'s `JsonStorageAdapter`.

**File**: `.vibe-analytics/data.json`

```typescript
interface AnalyticsData {
  lastSync: string;
  repo: {
    owner: string;
    name: string;
  };
  snapshots: {
    [date: string]: { // YYYY-MM-DD
      deploymentCount: number;
      leadTimeMinutes: number[]; // Array of lead times for that day
      cycleTimeMinutes: number[];
      incidents: {
        count: number;
        mttrMinutes: number[];
      };
    };
  };
  // Cache raw entities to avoid re-fetching everything
  cache: {
    latestPrCursor: string;
    latestReleaseCursor: string;
  };
}
```

## 5. CLI Command Structure

The tool will expose the following commands:

*   `vibe analytics init`: Configure repo owner, name, and incident labels.
*   `vibe analytics sync`: Fetch latest data from GitHub and update local storage.
*   `vibe analytics report`: Display metrics table.
    *   Options: `--period <days>` (default 30), `--json`.
*   `vibe analytics status`: Show when data was last synced.

**Example Output (`vibe analytics report`):**

```
Vibe Analytics Report (Last 30 Days)
------------------------------------
Deployment Frequency:  Daily (0.8/day)  [ELITE]
Lead Time for Changes: 48 hours         [MEDIUM]
Change Failure Rate:   5%               [HIGH]
Time to Restore:       4 hours          [LOW]
Cycle Time:            24 hours
```

## 6. Implementation Plan (Next Steps)

1.  **Setup**: Initialize `vibe-analytics` package structure.
2.  **Shared Libs**: Symlink or import `GitHubClient` and `JsonStorageAdapter` from `vibe-dev` (or refactor to shared package if allowed, otherwise duplicate for now/use relative import).
3.  **Data Layer**: Implement `AnalyticsService` to handle fetching and calculation.
4.  **CLI Layer**: Implement commands using `commander` (similar to `vibe-dev`).
