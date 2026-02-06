# Phase 2: GitHub GraphQL Client

**Priority:** High
**Status:** Pending

## Overview
Implement the data fetching layer using the GitHub GraphQL API. This layer is responsible for efficiently retrieving Pull Requests, Commits, Reviews, and Releases.

## Requirements
- Authenticate with GitHub using `octokit`.
- Implement `GitHubClient` class.
- Design GraphQL queries to fetch necessary data in minimal round trips.
- Handle pagination automatically.
- Type-safe responses.

## Key Insights
- **GraphQL vs REST**: Using GraphQL is mandatory to avoid the N+1 problem when fetching PR timelines and reviews.
- **Pagination**: Use `@octokit/plugin-paginate-graphql` to handle fetching large datasets (e.g., "last 90 days of PRs").

## Architecture
- **`src/lib/github-client.ts`**: Main client wrapper.
- **`src/lib/queries.ts`**: GraphQL query strings.
- **`src/types/github.ts`**: TypeScript interfaces for GraphQL responses.

## Implementation Steps

1.  **Install Dependencies**
    - `npm install octokit @octokit/plugin-paginate-graphql`

2.  **Define Types**
    - Create interfaces for `PullRequest`, `Commit`, `Review`, `Release` based on the GraphQL schema we need.

3.  **Implement Queries**
    - Write the `GetRepoMetrics` query:
      - `pullRequests`: `createdAt`, `mergedAt`, `additions`, `deletions`, `commits`, `reviews`.
      - `releases`: `createdAt`, `tagName`.

4.  **Build Client**
    - Initialize Octokit with auth token (from env `GITHUB_TOKEN`).
    - Create method `fetchRepoData(owner: string, repo: string, since: Date): Promise<RepoData>`.
    - Implement error handling (401, 403, 404).

## Success Criteria
- Can fetch the last 100 PRs and Releases from a public repo (e.g., `facebook/react`).
- Data is correctly typed and structured in the response.
- Pagination works for repos with >100 items.
