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
