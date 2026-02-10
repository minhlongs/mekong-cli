import { BaseAgent } from './base-agent.js';
import { AgentResult, OptimizationResult } from '../types/index.js';
import { GitService } from '../services/git-service.js';

interface DeployOptions {
  autoCommit?: boolean;
  autoPush?: boolean;
  commitMessage?: string;
}

export class DeployAgent extends BaseAgent {
  readonly name = 'DeployAgent';
  
  protected async run(): Promise<Partial<AgentResult>> {
    const { app } = this.context;
    const results = this.context.optimizationResults as OptimizationResult[] | undefined;
    
    this.logger.info(`Deploying optimizations for ${app.name}...`);
    
    if (this.isDryRun()) {
      this.logger.info('Dry run - skipping deployment');
      return { success: true };
    }
    
    const git = new GitService(app.path);
    
    // Check if git repo
    if (!(await git.isGitRepo())) {
      this.logger.warn('Not a git repository, skipping deployment');
      return { success: false, error: new Error('Not a git repo') };
    }
    
    // Stage all changes
    await git.stageChanges('.');
    
    // Check if there are changes to commit
    if (!(await git.hasUncommittedChanges())) {
      this.logger.info('No changes to deploy');
      return { success: true };
    }
    
    // Create commit message
    const message = this.generateCommitMessage(results);
    
    // Commit
    await git.commit(message);
    this.logger.info(`Committed: ${message.split('\n')[0]}`);
    
    // Optionally push
    if (process.env.AUTO_PUSH === 'true') {
      const currentBranch = await git.getCurrentBranch();
      await git.push('origin', currentBranch);
      this.logger.info('Pushed to remote');
    }
    
    return { success: true };
  }
  
  private generateCommitMessage(results: OptimizationResult[] | undefined): string {
    if (!results || results.length === 0) {
      return 'chore: build optimization';
    }
    
    const first = results[0];
    const totalSizeImprovement = results.reduce(
      (sum, r) => sum + r.improvement.sizePercent,
      0
    );
    const totalDurationImprovement = results.reduce(
      (sum, r) => sum + r.improvement.durationPercent,
      0
    );
    
    const lines = [
      `perf(${first.appName}): optimize build performance`,
      '',
      'Applied optimizations:',
      ...results.map(r => `- ${r.strategy}: ${r.improvement.sizePercent.toFixed(1)}% size, ${r.improvement.durationPercent.toFixed(1)}% time`),
      '',
      `Total improvement: ${totalSizeImprovement.toFixed(1)}% size, ${totalDurationImprovement.toFixed(1)}% time`,
    ];
    
    return lines.join('\n');
  }
}
