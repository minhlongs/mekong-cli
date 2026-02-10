// Asset types supported
export type AssetType = 'js' | 'css' | 'image' | 'font' | 'other';

// Individual asset metrics
export interface AssetMetrics {
  name: string;
  size: number;
  gzipSize: number;
  type: AssetType;
}

// Bundle metrics for analysis
export interface BundleMetrics {
  totalSize: number;
  gzipSize: number;
  assets: AssetMetrics[];
  chunks: string[];
}

// Lighthouse performance metrics
export interface LighthouseMetrics {
  performance: number;
  accessibility: number;
  bestPractices: number;
  seo: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  timeToInteractive: number;
  totalBlockingTime: number;
}

// Build metrics collected from each build
export interface BuildMetrics {
  appName: string;
  duration: number;
  bundleSize: number;
  assets: AssetMetrics[];
  timestamp: Date;
  success: boolean;
  error?: string;
}

// Optimization result after applying strategies
export interface OptimizationResult {
  appName: string;
  strategy: string;
  before: BuildMetrics;
  after: BuildMetrics;
  improvement: {
    durationPercent: number;
    sizePercent: number;
  };
  timestamp: Date;
}
