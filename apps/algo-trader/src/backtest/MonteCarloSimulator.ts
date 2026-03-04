/**
 * Monte Carlo Simulator for Backtesting
 * Evaluates strategy robustness through randomized market simulations
 */

export interface MonteCarloConfig {
  simulationCount: number; // Number of simulation iterations
  randomizeReturns?: boolean; // Whether to randomize returns
  randomizeTiming?: boolean; // Whether to randomize trade timing
  randomizeEntryPrices?: boolean; // Whether to randomize entry prices
  shuffleMethod?: 'block' | 'bootstrap' | 'random_walk'; // Method to generate synthetic data
  blockSize?: number; // Block size for block bootstrap (if applicable)
  volatilityAdjustment?: number; // Factor to adjust volatility in simulations
}

export interface MonteCarloResult {
  baselinePerformance: any; // Original strategy performance
  simulatedResults: any[]; // Results from each simulation
  confidenceIntervals: {
    lower: number; // Lower bound of confidence interval
    upper: number; // Upper bound of confidence interval
  };
  probabilityOfSuccess: number; // Probability of achieving target return
  worstCaseScenario: any; // Worst performing simulation
  bestCaseScenario: any; // Best performing simulation
  performanceDistribution: {
    mean: number;
    median: number;
    stdDev: number;
    skewness: number;
    kurtosis: number;
  };
}

export class MonteCarloSimulator {
  /**
   * Run Monte Carlo simulation to assess strategy robustness
   * @param baselineResult Original backtest result
   * @param historicalData Historical market data used in original test
   * @param strategyFn Function that executes the trading strategy
   * @param config Monte Carlo configuration
   * @returns Monte Carlo simulation results
   */
  static async runSimulation(
    baselineResult: any,
    historicalData: any[],
    strategyFn: (data: any[]) => Promise<any>,
    config: MonteCarloConfig
  ): Promise<MonteCarloResult> {
    const results: any[] = [];

    // Run the baseline simulation once to confirm the original result
    const baselineSimulation = await strategyFn(historicalData);
    results.push(baselineSimulation);

    // Generate and run multiple simulations
    for (let i = 1; i < config.simulationCount; i++) {
      try {
        // Generate synthetic market data based on the chosen method
        const syntheticData = this.generateSyntheticData(
          historicalData,
          config
        );

        // Apply the strategy to the synthetic data
        const simulatedResult = await strategyFn(syntheticData);
        results.push(simulatedResult);
      } catch (error) {
        // If a simulation fails, use a default result to maintain array size
        console.warn(`Simulation ${i} failed:`, error);
        results.push({
          totalReturn: 0,
          sharpeRatio: 0,
          maxDrawdown: 0,
          totalTrades: 0,
          winRate: 0
        });
      }
    }

    // Calculate statistics from the simulation results
    const returnValues = results.map(r => r.totalReturn || 0);
    const sortedReturns = [...returnValues].sort((a, b) => a - b);

    // Calculate confidence intervals (95% by default)
    const confidenceLevel = 0.95;
    const lowerPercentile = (1 - confidenceLevel) / 2;
    const upperPercentile = 1 - lowerPercentile;

    const lowerIndex = Math.floor(lowerPercentile * sortedReturns.length);
    const upperIndex = Math.floor(upperPercentile * sortedReturns.length);

    // Calculate performance distribution statistics
    const mean = returnValues.reduce((sum, val) => sum + val, 0) / returnValues.length;
    const variance = returnValues.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (returnValues.length - 1);
    const stdDev = Math.sqrt(variance);

    // Calculate skewness and kurtosis
    let sumCubedDeviations = 0;
    let sumFourthDeviations = 0;
    for (const value of returnValues) {
      const normalizedDiff = (value - mean) / stdDev;
      sumCubedDeviations += Math.pow(normalizedDiff, 3);
      sumFourthDeviations += Math.pow(normalizedDiff, 4);
    }
    const skewness = (sumCubedDeviations / returnValues.length);
    const kurtosis = (sumFourthDeviations / returnValues.length) - 3; // Excess kurtosis

    // Calculate probability of success (positive returns)
    const successfulRuns = returnValues.filter(ret => ret > 0).length;
    const probabilityOfSuccess = successfulRuns / returnValues.length;

    // Find best and worst case scenarios
    const worstCaseIdx = returnValues.indexOf(Math.min(...returnValues));
    const bestCaseIdx = returnValues.indexOf(Math.max(...returnValues));

    return {
      baselinePerformance: baselineSimulation,
      simulatedResults: results,
      confidenceIntervals: {
        lower: sortedReturns[lowerIndex],
        upper: sortedReturns[upperIndex]
      },
      probabilityOfSuccess,
      worstCaseScenario: results[worstCaseIdx],
      bestCaseScenario: results[bestCaseIdx],
      performanceDistribution: {
        mean,
        median: sortedReturns[Math.floor(sortedReturns.length / 2)],
        stdDev,
        skewness,
        kurtosis
      }
    };
  }

  /**
   * Generate synthetic market data using specified method
   */
  private static generateSyntheticData(
    originalData: any[],
    config: MonteCarloConfig
  ): any[] {
    switch (config.shuffleMethod || 'bootstrap') {
      case 'block':
        return this.blockBootstrap(originalData, config.blockSize || 10);
      case 'bootstrap':
        return this.bootStrapSampling(originalData);
      case 'random_walk':
        return this.randomWalkModel(originalData, config.volatilityAdjustment || 1);
      default:
        return this.bootStrapSampling(originalData);
    }
  }

  /**
   * Block bootstrap - preserves temporal dependencies
   */
  private static blockBootstrap(data: any[], blockSize: number): any[] {
    const result = [];
    const n = data.length;

    // Calculate how many blocks we need
    const numBlocks = Math.ceil(n / blockSize);

    // Create blocks
    const blocks = [];
    for (let i = 0; i < n; i += blockSize) {
      blocks.push(data.slice(i, Math.min(i + blockSize, n)));
    }

    // Randomly sample blocks with replacement
    for (let i = 0; i < numBlocks; i++) {
      const randomBlock = blocks[Math.floor(Math.random() * blocks.length)];
      result.push(...randomBlock);
    }

    // Trim to original length
    return result.slice(0, n);
  }

  /**
   * Regular bootstrap sampling
   */
  private static bootStrapSampling(data: any[]): any[] {
    const result = [];
    const n = data.length;

    // Sample with replacement
    for (let i = 0; i < n; i++) {
      const randomIndex = Math.floor(Math.random() * n);
      result.push({ ...data[randomIndex] }); // Shallow copy to avoid reference issues
    }

    return result;
  }

  /**
   * Random walk model with volatility adjustment
   */
  private static randomWalkModel(data: any[], volatilityAdjustment: number): any[] {
    if (data.length < 2) return [...data];

    // Calculate empirical return statistics
    const returns: number[] = [];
    for (let i = 1; i < data.length; i++) {
      const prevPrice = data[i-1].close || data[i-1].price;
      const currPrice = data[i].close || data[i].price;

      if (prevPrice && currPrice) {
        returns.push((currPrice - prevPrice) / prevPrice);
      }
    }

    if (returns.length === 0) return [...data];

    const meanReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdDevReturn = this.calculateStdDev(returns, meanReturn);

    // Adjust volatility
    const adjustedStdDev = stdDevReturn * volatilityAdjustment;

    // Generate new prices based on random walk
    const result = [{ ...data[0] }];
    let currentPrice = data[0].close || data[0].price || 100; // Default to 100 if no price

    for (let i = 1; i < data.length; i++) {
      // Generate random return based on normal distribution
      const randomReturn = this.sampleNormal(meanReturn, adjustedStdDev);
      const newPrice = currentPrice * (1 + randomReturn);

      // Create new data point with modified price but keeping other properties
      const newDataPoint = { ...data[i] };
      if (newDataPoint.close !== undefined) newDataPoint.close = newPrice;
      if (newDataPoint.price !== undefined) newDataPoint.price = newPrice;

      result.push(newDataPoint);
      currentPrice = newPrice;
    }

    return result;
  }

  /**
   * Calculate standard deviation
   */
  private static calculateStdDev(values: number[], mean: number): number {
    const squaredDifferences = values.map(value => Math.pow(value - mean, 2));
    const variance = squaredDifferences.reduce((sum, val) => sum + val, 0) / (values.length - 1);
    return Math.sqrt(variance);
  }

  /**
   * Sample from normal distribution using Box-Muller transform
   */
  private static sampleNormal(mean: number, stdDev: number): number {
    // Box-Muller transform to generate normal random variables
    const u1 = Math.random();
    const u2 = Math.random();
    const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);

    // Scale to desired mean and std dev
    return mean + z * stdDev;
  }

  /**
   * Evaluate strategy robustness based on Monte Carlo results
   */
  static evaluateRobustness(result: MonteCarloResult, targetReturn: number = 0): {
    robustnessScore: number; // Higher is better
    riskOfSpuriousness: number; // Lower is better
    confidenceInPerformance: number; // Higher is better
  } {
    // Robustness based on consistency of results across simulations
    const { mean, stdDev } = result.performanceDistribution;

    // Calculate coefficient of variation (lower is more consistent)
    const cv = mean !== 0 ? stdDev / Math.abs(mean) : Infinity;

    // Robustness score: 1/(1+cv) to ensure it's between 0 and 1
    const robustnessScore = stdDev !== 0 ? 1 / (1 + cv) : 1;

    // Risk of spuriousness: probability that good performance is due to chance
    // Lower probability of positive returns suggests higher risk of spuriousness
    const riskOfSpuriousness = 1 - result.probabilityOfSuccess;

    // Confidence in performance: how far are confidence intervals from target
    const distanceFromTarget = Math.min(
      Math.abs(result.confidenceIntervals.lower - targetReturn),
      Math.abs(result.confidenceIntervals.upper - targetReturn)
    );

    // Normalize confidence (higher confidence intervals closer to target = higher confidence)
    const confidenceInPerformance = 1 / (1 + distanceFromTarget);

    return {
      robustnessScore,
      riskOfSpuriousness,
      confidenceInPerformance
    };
  }
}