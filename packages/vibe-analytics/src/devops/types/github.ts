export interface GraphQLCommit {
  commit: {
    committedDate: string;
  };
}

export interface GraphQLReview {
  createdAt: string;
  state: string;
  author: {
    login: string;
  };
}

export interface GraphQLPullRequest {
  number: number;
  title: string;
  state: string;
  createdAt: string;
  mergedAt: string | null;
  closedAt: string | null;
  additions: number;
  deletions: number;
  url: string;
  author: {
    login: string;
  };
  commits: {
    nodes: GraphQLCommit[];
  };
  reviews: {
    nodes: GraphQLReview[];
  };
}

export interface GraphQLRelease {
  name: string;
  tagName: string;
  createdAt: string;
  publishedAt: string;
  isPrerelease: boolean;
  isDraft: boolean;
  url: string;
}

export interface GraphQLRepositoryResponse {
  repository: {
    pullRequests: {
      nodes: GraphQLPullRequest[];
      pageInfo: {
        hasNextPage: boolean;
        endCursor: string;
      };
    };
    releases: {
      nodes: GraphQLRelease[];
      pageInfo: {
        hasNextPage: boolean;
        endCursor: string;
      };
    };
  };
}

export interface RepoMetricsData {
  pullRequests: GraphQLPullRequest[];
  releases: GraphQLRelease[];
}
