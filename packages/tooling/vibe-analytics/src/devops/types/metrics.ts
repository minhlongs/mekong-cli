export interface WorkflowRun {
  id: number;
  name: string;
  status: string;
  conclusion: string | null;
  created_at: string;
  updated_at: string;
  head_branch: string;
  head_sha: string;
  html_url: string;
}

export interface PullRequest {
  id: number;
  number: number;
  title: string;
  state: string;
  created_at: string;
  updated_at: string;
  merged_at: string | null;
  merged: boolean;
  merged_by?: { login: string } | null;
  additions: number;
  deletions: number;
  changed_files: number;
  user: { login: string };
  html_url: string;
}

export interface RepoData {
  owner: string;
  repo: string;
  pullRequests: PullRequest[];
  workflowRuns: WorkflowRun[];
}

export interface MetricResult {
  value: number;
  unit: string;
  label: string;
  description?: string;
  rating?: 'Elite' | 'High' | 'Medium' | 'Low';
}

export interface DoraMetrics {
  deploymentFrequency: MetricResult;
  leadTimeForChanges: MetricResult;
  changeFailureRate: MetricResult;
  timeToRestoreService: MetricResult;
}

export interface VelocityMetrics {
  cycleTime: MetricResult;
  prPickupTime: MetricResult;
  prReviewTime: MetricResult;
  prMergeTime: MetricResult;
  prSize: MetricResult;
}

export interface MetricsReport {
  period: {
    start: Date;
    end: Date;
    days: number;
  };
  dora: DoraMetrics;
  velocity: VelocityMetrics;
}
