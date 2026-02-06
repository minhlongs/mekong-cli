import { RepoMetricsData, GraphQLPullRequest, GraphQLRelease } from "../types/github.js";
import { MetricsReport, MetricResult, DoraMetrics, VelocityMetrics } from "../types/metrics.js";

export class MetricsEngine {
  calculate(data: RepoMetricsData, days: number): MetricsReport {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    const dora = this.calculateDora(data, days);
    const velocity = this.calculateVelocity(data);

    return {
      period: {
        start: startDate,
        end: endDate,
        days,
      },
      dora,
      velocity,
    };
  }

  private calculateDora(data: RepoMetricsData, days: number): DoraMetrics {
    // 1. Deployment Frequency
    // Count releases in the period
    const releaseCount = data.releases.length;
    const deploymentsPerDay = releaseCount / days;

    // Rating (simplified based on DORA 2023)
    let dfRating: 'Elite' | 'High' | 'Medium' | 'Low' = 'Low';
    if (deploymentsPerDay >= 1) dfRating = 'Elite'; // On demand (multiple per day)
    else if (deploymentsPerDay >= 1/7) dfRating = 'High'; // Once per week to once per month
    else if (deploymentsPerDay >= 1/30) dfRating = 'Medium'; // Once per month to once per 6 months

    // 2. Lead Time for Changes
    // Time from commit to release.
    // Approx: Time from PR merged to Release is hard without linking.
    // Proxy: Time from first commit in PR to PR merge (Lead Time to Merge).
    // Real DORA is Commit -> Prod. We will use Commit -> Merge as a proxy for "Development Lead Time"
    const leadTimes = data.pullRequests
      .filter(pr => pr.mergedAt && pr.commits.nodes.length > 0)
      .map(pr => {
        const firstCommit = new Date(pr.commits.nodes[0].commit.committedDate);
        const mergedAt = new Date(pr.mergedAt!);
        return (mergedAt.getTime() - firstCommit.getTime()) / (1000 * 60 * 60); // hours
      });

    const medianLeadTimeHours = this.median(leadTimes);
    const leadTimeDays = medianLeadTimeHours / 24;

    // Rating
    let ltRating: 'Elite' | 'High' | 'Medium' | 'Low' = 'Low';
    if (leadTimeDays < 1) ltRating = 'Elite'; // Less than one day
    else if (leadTimeDays < 7) ltRating = 'High'; // Between one day and one week
    else if (leadTimeDays < 30) ltRating = 'Medium'; // Between one week and one month

    // 3. Change Failure Rate
    // Look for releases with "hotfix" in name or tag
    const hotfixes = data.releases.filter(r =>
      r.name?.toLowerCase().includes('hotfix') ||
      r.tagName?.toLowerCase().includes('hotfix')
    ).length;

    const failureRate = releaseCount > 0 ? (hotfixes / releaseCount) * 100 : 0;

    let cfrRating: 'Elite' | 'High' | 'Medium' | 'Low' = 'Low';
    if (failureRate < 5) cfrRating = 'Elite';
    else if (failureRate < 10) cfrRating = 'High';
    else if (failureRate < 15) cfrRating = 'Medium';

    // 4. Time to Restore Service (MTTR)
    // Hard to calculate without incident data. Placeholder.
    // We could look for "fix" PRs and check time from issue creation, but that requires issues.
    // For now, we'll return N/A or 0.

    return {
      deploymentFrequency: {
        value: Number(deploymentsPerDay.toFixed(2)),
        unit: 'deployments/day',
        label: 'Deployment Frequency',
        rating: dfRating
      },
      leadTimeForChanges: {
        value: Number(leadTimeDays.toFixed(2)),
        unit: 'days',
        label: 'Lead Time for Changes',
        rating: ltRating
      },
      changeFailureRate: {
        value: Number(failureRate.toFixed(2)),
        unit: '%',
        label: 'Change Failure Rate',
        rating: cfrRating
      },
      timeToRestoreService: {
        value: 0,
        unit: 'hours',
        label: 'Time to Restore Service',
        description: 'Not available (requires incident data)'
      }
    };
  }

  private calculateVelocity(data: RepoMetricsData): VelocityMetrics {
    const prs = data.pullRequests.filter(pr => pr.mergedAt);

    // Pickup Time: Created -> First Review
    const pickupTimes = prs.map(pr => {
      if (pr.reviews.nodes.length === 0) return 0;
      // Find first non-author review? GitHub returns reviews chronological.
      const firstReview = new Date(pr.reviews.nodes[0].createdAt);
      const created = new Date(pr.createdAt);
      return Math.max(0, (firstReview.getTime() - created.getTime()) / (1000 * 60 * 60)); // hours
    }).filter(t => t > 0);

    // Review Time: First Review -> Merged
    const reviewTimes = prs.map(pr => {
      if (pr.reviews.nodes.length === 0) return 0;
      const firstReview = new Date(pr.reviews.nodes[0].createdAt);
      const merged = new Date(pr.mergedAt!);
      return Math.max(0, (merged.getTime() - firstReview.getTime()) / (1000 * 60 * 60)); // hours
    }).filter(t => t > 0);

    // Merge Time: Created -> Merged (Total Cycle)
    const mergeTimes = prs.map(pr => {
      const created = new Date(pr.createdAt);
      const merged = new Date(pr.mergedAt!);
      return (merged.getTime() - created.getTime()) / (1000 * 60 * 60); // hours
    });

    // Cycle Time: First Commit -> Merged
    const cycleTimes = prs.map(pr => {
      if (pr.commits.nodes.length === 0) return 0;
      const firstCommit = new Date(pr.commits.nodes[0].commit.committedDate);
      const merged = new Date(pr.mergedAt!);
      return (merged.getTime() - firstCommit.getTime()) / (1000 * 60 * 60); // hours
    });

    const sizes = prs.map(pr => pr.additions + pr.deletions);

    return {
      cycleTime: {
        value: Number(this.median(cycleTimes).toFixed(2)),
        unit: 'hours',
        label: 'Cycle Time'
      },
      prPickupTime: {
        value: Number(this.median(pickupTimes).toFixed(2)),
        unit: 'hours',
        label: 'PR Pickup Time'
      },
      prReviewTime: {
        value: Number(this.median(reviewTimes).toFixed(2)),
        unit: 'hours',
        label: 'PR Review Time'
      },
      prMergeTime: {
        value: Number(this.median(mergeTimes).toFixed(2)),
        unit: 'hours',
        label: 'PR Merge Time'
      },
      prSize: {
        value: Math.round(this.median(sizes)),
        unit: 'lines',
        label: 'PR Size'
      }
    };
  }

  private median(values: number[]): number {
    if (values.length === 0) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const half = Math.floor(sorted.length / 2);
    if (sorted.length % 2) return sorted[half];
    return (sorted[half - 1] + sorted[half]) / 2.0;
  }
}
