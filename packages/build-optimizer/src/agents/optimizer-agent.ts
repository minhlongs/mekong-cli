import { BaseAgent } from './base-agent.js';
import { AgentResult, OptimizationResult, AppConfig } from '../types/index.js';
import { BuildService } from '../services/build-service.js';
import { GitService } from '../services/git-service.js';
import { OptimizationFailedError } from '../utils/errors.js';
import { Strategy } from '../strategies/index.js';

export class OptimizerAgent extends BaseAgent {
  readonly name = 'OptimizerAgent';
  private buildService = new BuildService();
  private strategies: Strategy[] = [];
  
  registerStrategy(strategy: Strategy): void {
    this.strategies.push(strategy);
  }
  
  protected async run(): Promise<Partial<AgentResult>> {
    const { app, config, metrics: initialMetrics } = this.context;
    
    if (!initialMetrics) {
      throw new OptimizationFailedError('No baseline metrics available');
    }
    
    this.logger.info(`Optimizing ${app.name}...`);
    
    const git = new GitService(app.path);
    const results: OptimizationResult[] = [];
    
    // Create feature branch if not dry run
    if (!this.isDryRun()) {
      const branchName = `mekong/optimize-${app.name}-${Date.now()}`;
      await git.createBranch(branchName);
      this.logger.debug(`Created branch: ${branchName}`);
    }
    
    // Apply each enabled strategy
    for (const strategy of this.strategies) {
      if (!this.isStrategyEnabled(strategy.name, config.strategies)) {
        this.logger.debug(`Skipping disabled strategy: ${strategy.name}`);
        continue;
      }
      
      // Check if strategy can be applied
      const canApply = await strategy.canApply(app);
      if (!canApply) {
        this.logger.debug(`Strategy ${strategy.name} cannot be applied to ${app.name}`);
        continue;
      }
      
      this.logger.info(`Applying strategy: ${strategy.name}`);
      
      try {
        // Apply optimization
        await strategy.apply(app, this.logger);
        
        // Rebuild to measure improvement
        const newMetrics = await this.buildService.build({
          app,
          cwd: app.path,
        });
        
        // Calculate improvement
        const result: OptimizationResult = {
          appName: app.name,
          strategy: strategy.name,
          before: initialMetrics,
          after: newMetrics,
          improvement: {
            durationPercent: this.calcImprovement(
              initialMetrics.duration,
              newMetrics.duration
            ),
            sizePercent: this.calcImprovement(
              initialMetrics.bundleSize,
              newMetrics.bundleSize
            ),
          },
          timestamp: new Date(),
        };
        
        results.push(result);
        this.logger.info(
          `Strategy ${strategy.name}: ${result.improvement.sizePercent.toFixed(1)}% size reduction, ${result.improvement.durationPercent.toFixed(1)}% time reduction`
        );
        
      } catch (error) {
        this.logger.error(`Strategy ${strategy.name} failed`, { error });
        
        // Rollback on failure
        if (!this.isDryRun()) {
          await this.rollback(git, strategy, app);
        }
        
        throw new OptimizationFailedError(
          `Strategy ${strategy.name} failed`,
          { strategy: strategy.name, error: String(error) }
        );
      }
    }
    
    return { data: results, metrics: results.length > 0 ? results[results.length - 1].after : initialMetrics };
  }
  
  private isStrategyEnabled(
    name: string,
    config: { treeShaking: boolean; codeSplitting: boolean; compression: boolean; caching: boolean }
  ): boolean {
    const strategyMap: Record<string, keyof typeof config> = {
      'tree-shaking': 'treeShaking',
      'code-splitting': 'codeSplitting',
      'compression': 'compression',
      'caching': 'caching',
    };
    
    const key = strategyMap[name];
    return key ? config[key] : true;
  }
  
  private calcImprovement(before: number, after: number): number {
    if (before === 0) return 0;
    return ((before - after) / before) * 100;
  }
  
  private async rollback(git: GitService, strategy: Strategy, app: AppConfig): Promise<void> {
    this.logger.warn('Rolling back changes...');
    try {
      await strategy.rollback(app, this.logger);
    } catch {
      this.logger.warn('Strategy rollback failed, performing git reset...');
      await git.resetHard('HEAD');
    }
  }
}
