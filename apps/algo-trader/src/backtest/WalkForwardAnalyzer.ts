/**
 * Walk-Forward Analysis for Backtesting
 * Implements expanding and rolling window validation techniques
 */

export interface WalkForwardConfig {
  inSamplePeriod: number; // Number of data points for in-sample training
  outOfSamplePeriod: number; // Number of data points for out-of-sample testing
  minSamplePeriod?: number; // Minimum number of data points required
  walkMode: 'expanding' | 'rolling'; // Expanding or rolling window approach
  reoptimizeInterval?: number; // How often to re-optimize parameters (for rolling)
}

export interface WalkForwardSegment {
  segmentId: number;
  startDate: Date;
  endDate: Date;
  inSampleData: any[]; // Generic type for historical data
  outOfSampleData: any[]; // Generic type for test data
  isTraining: boolean; // Whether this segment is for training or testing
  performance?: any; // Performance metrics for this segment
}

export interface WalkForwardResult {
  segments: WalkForwardSegment[];
  overallPerformance: any; // Overall performance metrics
  outOfSampleRatio: number; // Ratio of out-of-sample to total data
  performanceConsistency: number; // Measure of performance stability across segments
}

export class WalkForwardAnalyzer {
  /**
   * Perform walk-forward analysis on historical data
   * @param historicalData Historical market data
   * @param config Walk-forward configuration
   * @returns Walk-forward analysis results
   */
  static async performWalkForwardAnalysis(
    historicalData: any[],
    config: WalkForwardConfig
  ): Promise<WalkForwardResult> {
    const minRequiredPoints = config.minSamplePeriod || config.inSamplePeriod;
    if (historicalData.length < minRequiredPoints + config.outOfSamplePeriod) {
      throw new Error(`Insufficient data for walk-forward analysis. Need at least ${minRequiredPoints + config.outOfSamplePeriod} data points, got ${historicalData.length}`);
    }

    const segments: WalkForwardSegment[] = [];
    let currentIndex = 0;
    let segmentId = 0;

    // Calculate the number of complete segments we can create
    const totalPeriod = config.inSamplePeriod + config.outOfSamplePeriod;
    const maxSegments = Math.floor((historicalData.length - minRequiredPoints) / config.outOfSamplePeriod);

    while (currentIndex + totalPeriod <= historicalData.length && segments.length < maxSegments) {
      // Determine in-sample and out-of-sample periods
      let inSampleEndIndex: number;

      if (config.walkMode === 'expanding') {
        // For expanding window, in-sample grows with each segment
        inSampleEndIndex = minRequiredPoints + (segments.length * config.outOfSamplePeriod) + config.inSamplePeriod - 1;
        inSampleEndIndex = Math.min(inSampleEndIndex, historicalData.length - config.outOfSamplePeriod);
      } else {
        // For rolling window, in-sample is fixed size
        inSampleEndIndex = currentIndex + config.inSamplePeriod - 1;
      }

      const inSampleStartIndex = config.walkMode === 'expanding'
        ? 0
        : currentIndex;

      const outOfSampleStartIndex = inSampleEndIndex + 1;
      const outOfSampleEndIndex = outOfSampleStartIndex + config.outOfSamplePeriod - 1;

      // Check bounds
      if (outOfSampleEndIndex >= historicalData.length) {
        break;
      }

      // Extract data for this segment
      const inSampleData = historicalData.slice(inSampleStartIndex, inSampleEndIndex + 1);
      const outOfSampleData = historicalData.slice(outOfSampleStartIndex, outOfSampleEndIndex + 1);

      // Create segment
      const segment: WalkForwardSegment = {
        segmentId: segmentId++,
        startDate: new Date(Math.min(
          ...inSampleData.concat(outOfSampleData).map(d => new Date(d.timestamp || d.date).getTime())
        )),
        endDate: new Date(Math.max(
          ...inSampleData.concat(outOfSampleData).map(d => new Date(d.timestamp || d.date).getTime())
        )),
        inSampleData,
        outOfSampleData,
        isTraining: true // Initially marked as training, may be updated later
      };

      segments.push(segment);

      // Move to next window
      if (config.walkMode === 'expanding') {
        currentIndex = outOfSampleEndIndex + 1;
      } else {
        // For rolling window, shift by the out-of-sample period
        currentIndex += config.outOfSamplePeriod;

        // Check if we should re-optimize based on interval
        if (config.reoptimizeInterval && (segments.length % config.reoptimizeInterval === 0)) {
          // Re-optimization would happen here in a real implementation
          // This is where you would re-run parameter optimization
        }
      }
    }

    // Process segments - alternate between training and testing
    let isTrainingSegment = true;
    for (const segment of segments) {
      segment.isTraining = isTrainingSegment;
      isTrainingSegment = !isTrainingSegment; // Alternate between training and testing
    }

    // Calculate overall results
    const outOfSampleSegments = segments.filter(s => !s.isTraining);
    const outOfSampleDataPoints = outOfSampleSegments.reduce((sum, s) => sum + s.outOfSampleData.length, 0);
    const outOfSampleRatio = outOfSampleDataPoints / historicalData.length;

    // Calculate performance consistency across segments
    const performanceValues = segments.map(s => s.performance?.totalReturn || 0).filter(v => v !== 0);
    let performanceConsistency = 1.0; // Default to perfect consistency

    if (performanceValues.length > 1) {
      const mean = performanceValues.reduce((sum, val) => sum + val, 0) / performanceValues.length;
      const variance = performanceValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / performanceValues.length;
      const stdDev = Math.sqrt(variance);

      // Consistency score based on coefficient of variation (lower is better)
      performanceConsistency = mean !== 0 ? 1 - (stdDev / Math.abs(mean)) : 1.0;
      performanceConsistency = Math.max(0, performanceConsistency); // Clamp to [0, 1]
    }

    return {
      segments,
      overallPerformance: {},
      outOfSampleRatio,
      performanceConsistency
    };
  }

  /**
   * Validates if a strategy passes walk-forward analysis criteria
   * @param result Walk-forward analysis result
   * @param minOutOfSampleRatio Minimum required out-of-sample ratio
   * @param minPerformanceConsistency Minimum required performance consistency
   * @returns Whether the strategy passes validation
   */
  static validateWalkForwardResult(
    result: WalkForwardResult,
    minOutOfSampleRatio: number = 0.2,
    minPerformanceConsistency: number = 0.5
  ): boolean {
    const passesRatio = result.outOfSampleRatio >= minOutOfSampleRatio;
    const passesConsistency = result.performanceConsistency >= minPerformanceConsistency;

    // Additional validation: check if in-sample performance is not significantly better than out-of-sample
    const trainingSegments = result.segments.filter(s => s.isTraining && s.performance?.totalReturn !== undefined);
    const testingSegments = result.segments.filter(s => !s.isTraining && s.performance?.totalReturn !== undefined);

    if (trainingSegments.length > 0 && testingSegments.length > 0) {
      const avgTrainingReturn = trainingSegments.reduce((sum, s) => sum + s.performance.totalReturn, 0) / trainingSegments.length;
      const avgTestingReturn = testingSegments.reduce((sum, s) => sum + s.performance.totalReturn, 0) / testingSegments.length;

      // Check for overfitting (training significantly better than testing)
      const overfittingRatio = avgTestingReturn !== 0 ? avgTrainingReturn / avgTestingReturn : Infinity;
      const passesOverfitting = overfittingRatio <= 2.0; // Training performance shouldn't be more than 2x testing

      return passesRatio && passesConsistency && passesOverfitting;
    }

    return passesRatio && passesConsistency;
  }

  /**
   * Creates a walk-forward configuration optimized for different market regimes
   * @param marketRegime Current market regime
   * @returns Optimized walk-forward configuration
   */
  static createAdaptiveConfig(marketRegime: 'trending' | 'mean-reverting' | 'volatile' | 'quiet'): WalkForwardConfig {
    // Different configurations based on market regime
    switch (marketRegime) {
      case 'trending':
        // Longer periods to capture trend movements
        return {
          inSamplePeriod: 200, // More data for trend identification
          outOfSamplePeriod: 50,
          minSamplePeriod: 100,
          walkMode: 'rolling' as const,
          reoptimizeInterval: 10 // Re-optimize less frequently for stable trends
        };
      case 'mean-reverting':
        // Shorter periods to capture mean reversion
        return {
          inSamplePeriod: 100,
          outOfSamplePeriod: 25,
          minSamplePeriod: 50,
          walkMode: 'rolling' as const,
          reoptimizeInterval: 5 // More frequent re-optimization for mean reversion
        };
      case 'volatile':
        // Shorter periods to adapt to rapid changes
        return {
          inSamplePeriod: 75,
          outOfSamplePeriod: 20,
          minSamplePeriod: 40,
          walkMode: 'rolling' as const,
          reoptimizeInterval: 3 // Very frequent re-optimization for volatile markets
        };
      case 'quiet':
        // Moderate periods with conservative approach
        return {
          inSamplePeriod: 150,
          outOfSamplePeriod: 40,
          minSamplePeriod: 80,
          walkMode: 'expanding' as const,
          reoptimizeInterval: 15 // Less frequent re-optimization for stable markets
        };
      default:
        // Default configuration
        return {
          inSamplePeriod: 150,
          outOfSamplePeriod: 30,
          minSamplePeriod: 100,
          walkMode: 'rolling' as const,
          reoptimizeInterval: 7
        };
    }
  }
}