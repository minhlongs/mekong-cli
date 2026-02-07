# Research Report: DevOps/Engineering Metrics & Implementation Strategy

**Date:** 260206
**Context:** `vibe-analytics`
**Focus:** Lightweight, CLI-friendly DORA & Engineering Metrics for GitHub

## 1. Executive Summary

This report outlines the strategy for implementing engineering metrics (DORA, Cycle Time) within the `vibe-analytics` package. The recommended approach is to build a lightweight, custom extraction engine using the **GitHub GraphQL API** via `octokit`. Existing "all-in-one" open-source tools are often too heavy, abandoned, or require separate infrastructure. A custom TypeScript implementation ensures tight integration with `vibe-dev` and minimal dependencies.

## 2. Core Metrics Definitions

### 2.1 DORA Metrics (The "Big 4")
| Metric | Definition | Implementation Signal |
| :--- | :--- | :--- |
| **Deployment Frequency** | How often code is released to production. | Count of GitHub Releases or Tags matching a pattern (e.g., `v*`) per day/week. |
| **Lead Time for Changes** | Time from commit to running in production. | `timestamp(release) - timestamp(oldest_commit_in_release)` OR `timestamp(pr_merge) - timestamp(pr_first_commit)`. |
| **Change Failure Rate** | Percentage of deployments causing a failure in production. | `(Count of Hotfix Releases / Total Releases)` OR Labels like `bug` on issues linked to releases. |
| **Time to Restore Service** | Time to recover from a failure. | `timestamp(hotfix_close) - timestamp(incident_open)`. |

### 2.2 Operational Metrics (Velocity)
| Metric | Definition | Implementation Signal |
| :--- | :--- | :--- |
| **Cycle Time** | Total time from "first commit" to "deployment". | Breakdown: Coding Time + Pickup Time + Review Time + Deploy Time. |
| **PR Pickup Time** | Time from PR open to first review. | `pr.reviews[0].createdAt - pr.createdAt`. |
| **PR Merge Time** | Time from PR open to merge. | `pr.mergedAt - pr.createdAt`. |
| **PR Size** | Lines of code changed. | `pr.additions + pr.deletions` (Small PRs correlate with high velocity). |

## 3. Technology Strategy

### 3.1 Recommended Stack
*   **Language:** TypeScript (Node.js)
*   **API Client:** `octokit` (Official GitHub SDK) with `@octokit/plugin-paginate-graphql`.
*   **Data Source:** GitHub GraphQL API (v4). **Crucial** for performance. Retrieving PR timelines via REST is too chatty (N+1 problem). GraphQL allows fetching PRs + Reviews + Commits + Statuses in a single query.
*   **Storage (Optional):** SQLite or simple JSON dump for local analysis.

### 3.2 Evaluation of Existing Tools
*   **`linear-b`, `haystack`, `sleuth`**: Enterprise SaaS, not suitable for CLI/Local integration.
*   **`github-dora`**: Several small NPM packages exist but most are unmaintained/stale.
*   **`cdupuis/dora-metrics`**: Good reference implementation but Python-based.
*   **Recommendation:** **Build Custom**. The logic to calculate these metrics is essentially time-diff math on GitHub objects. A custom library in `vibe-analytics` provides the best DX for the CLI.

## 4. Implementation Plan (GraphQL)

### 4.1 Query Structure
We need to fetch Pull Requests with specific associated data:
```graphql
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, states: MERGED) {
      nodes {
        createdAt
        mergedAt
        additions
        deletions
        commits(first: 1) { nodes { commit { committedDate } } }
        reviews(first: 1) { nodes { createdAt } }
      }
    }
    releases(first: 100) {
      nodes {
        createdAt
        tag { name }
      }
    }
  }
}
```

### 4.2 Algorithm
1.  **Fetch Data**: Paginate through `pullRequests` and `releases` for the last 30/90 days.
2.  **Calculate Buckets**: Group by day/week.
3.  **Compute Diffs**:
    *   `Lead Time` = `mergedAt` - `commits[0].committedDate`
    *   `Pickup Time` = `reviews[0].createdAt` - `createdAt`
4.  **Aggregate**: Calculate Median/P95 (Averages are misleading for velocity).

## 5. Integration with vibe-dev
*   **New Package**: `packages/vibe-analytics`
*   **CLI Command**: `vibe metrics --repo owner/repo --period 30d`
*   **Output**: Console table + JSON report.

## 6. Open Questions
*   How do we identify "Production" failures for Change Failure Rate? (Convention: Look for "hotfix" in release names or specific labels on issues).
*   Do we support Mono-repos? (Tag filtering by prefix will be required).

## Sources
*   [Google Cloud DORA Research](https://cloud.google.com/blog/products/devops-sre/using-software-delivery-performance-metrics-for-better-results)
*   [GitHub GraphQL API Docs](https://docs.github.com/en/graphql)
*   [Thoughtworks Tech Radar: Four Key Metrics](https://www.thoughtworks.com/radar/techniques/four-key-metrics)
