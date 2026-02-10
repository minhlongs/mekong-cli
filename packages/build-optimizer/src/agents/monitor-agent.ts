import { BaseAgent } from './base-agent.js';
import { AgentResult, BuildMetrics } from '../types/index.js';
import { BuildService } from '../services/build-service.js';

export class MonitorAgent extends BaseAgent {
  readonly name = 'MonitorAgent';
  private buildService = new BuildService();
  
  protected async run(): Promise<Partial<AgentResult>> {
    const { app, config } = this.context;
    
    this.logger.info(`Monitoring ${app.name}...`);
    
    // Run clean build for accurate metrics
    const metrics = await this.buildService.build({
      app,
      cwd: app.path,
    });
    
    // Check thresholds
    this.checkThresholds(metrics, config.thresholds);
    
    // Log summary
    this.logSummary(metrics);
    
    return { metrics };
  }
  
  private checkThresholds(
    metrics: BuildMetrics,
    thresholds: { bundleSizeWarning: number; bundleSizeError: number; buildTimeWarning: number; buildTimeError: number }
  ): void {
    const sizeKB = metrics.bundleSize / 1024;
    const durationSec = metrics.duration / 1000;
    
    if (sizeKB > thresholds.bundleSizeError) {
      this.logger.warn(
        `Bundle size ${sizeKB.toFixed(0)}KB exceeds error threshold (${thresholds.bundleSizeError}KB)`
      );
    } else if (sizeKB > thresholds.bundleSizeWarning) {
      this.logger.warn(
        `Bundle size ${sizeKB.toFixed(0)}KB exceeds warning threshold (${thresholds.bundleSizeWarning}KB)`
      );
    }
    
    if (durationSec > thresholds.buildTimeError) {
      this.logger.warn(
        `Build time ${durationSec.toFixed(1)}s exceeds error threshold (${thresholds.buildTimeError}s)`
      );
    } else if (durationSec > thresholds.buildTimeWarning) {
      this.logger.warn(
        `Build time ${durationSec.toFixed(1)}s exceeds warning threshold (${thresholds.buildTimeWarning}s)`
      );
    }
  }
  
  private logSummary(metrics: BuildMetrics): void {
    const sizeMB = (metrics.bundleSize / 1024 / 1024).toFixed(2);
    const durationSec = (metrics.duration / 1000).toFixed(1);
    
    this.logger.info(`Build complete: ${sizeMB}MB in ${durationSec}s`);
    this.logger.debug(`Assets: ${metrics.assets.length} files`);
    
    // Log top 5 largest assets
    const sortedAssets = [...metrics.assets].sort((a, b) => b.size - a.size).slice(0, 5);
    if (sortedAssets.length > 0) {
      this.logger.debug('Largest assets:');
      for (const asset of sortedAssets) {
        const sizeKB = (asset.size / 1024).toFixed(1);
        this.logger.debug(`  ${asset.name}: ${sizeKB}KB (${asset.type})`);
      }
    }
  }
}
