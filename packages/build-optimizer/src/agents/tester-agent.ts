import { BaseAgent } from './base-agent.js';
import { AgentResult } from '../types/index.js';
import { BuildService } from '../services/build-service.js';
import { spawn } from 'child_process';
import { readFile } from 'fs/promises';
import { join } from 'path';

export class TesterAgent extends BaseAgent {
  readonly name = 'TesterAgent';
  private buildService = new BuildService();
  
  protected async run(): Promise<Partial<AgentResult>> {
    const { app } = this.context;
    
    this.logger.info(`Testing ${app.name}...`);
    
    const tests: Promise<boolean>[] = [];
    
    // Build test
    tests.push(this.testBuild());
    
    // Unit tests
    if (await this.hasScript('test')) {
      tests.push(this.testScript('test', 'Unit tests'));
    }
    
    // Lint
    if (await this.hasScript('lint')) {
      tests.push(this.testScript('lint', 'Linting'));
    }
    
    // Type check
    if (await this.hasScript('typecheck') || await this.hasScript('tsc')) {
      const typecheckScript = await this.hasScript('typecheck') ? 'typecheck' : 'tsc';
      tests.push(this.testScript(typecheckScript, 'Type checking'));
    }
    
    // Run all tests
    const results = await Promise.all(tests);
    const allPassed = results.every(r => r);
    
    if (!allPassed) {
      throw new Error('One or more tests failed');
    }
    
    this.logger.info('All tests passed');
    
    return { success: true };
  }
  
  private async testBuild(): Promise<boolean> {
    try {
      const { app } = this.context;
      await this.buildService.build({ app, cwd: app.path });
      this.logger.info('✓ Build test passed');
      return true;
    } catch (error) {
      this.logger.error('✗ Build test failed', { error: String(error) });
      return false;
    }
  }
  
  private async testScript(script: string, label: string): Promise<boolean> {
    const { app } = this.context;
    
    return new Promise((resolve) => {
      const child = spawn('npm', ['run', script], {
        cwd: app.path,
        stdio: 'pipe',
        shell: true,
      });

      child.stderr?.on('data', (data) => {
        this.logger.debug(`${label} output:`, data.toString().slice(0, 500));
      });

      child.on('close', (code) => {
        if (code === 0) {
          this.logger.info(`✓ ${label} passed`);
          resolve(true);
        } else {
          this.logger.error(`✗ ${label} failed`);
          resolve(false);
        }
      });
    });
  }
  
  private async hasScript(name: string): Promise<boolean> {
    const { app } = this.context;
    
    try {
      const packageJsonPath = join(app.path, 'package.json');
      const content = await readFile(packageJsonPath, 'utf-8');
      const pkg = JSON.parse(content);
      return name in (pkg.scripts || {});
    } catch {
      return false;
    }
  }
}
