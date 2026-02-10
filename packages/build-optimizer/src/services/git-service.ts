import { spawn } from 'child_process';
import { join } from 'path';

export class GitService {
  constructor(private cwd: string) {}
  
  async isGitRepo(): Promise<boolean> {
    try {
      await this.execGit(['rev-parse', '--git-dir']);
      return true;
    } catch {
      return false;
    }
  }
  
  async createBranch(branchName: string): Promise<void> {
    await this.execGit(['checkout', '-b', branchName]);
  }
  
  async stageChanges(path: string): Promise<void> {
    await this.execGit(['add', path]);
  }
  
  async commit(message: string): Promise<void> {
    await this.execGit(['commit', '-m', message]);
  }
  
  async push(remote = 'origin', branch?: string): Promise<void> {
    const args = ['push', remote];
    if (branch) args.push(branch);
    await this.execGit(args);
  }
  
  async stash(): Promise<void> {
    await this.execGit(['stash', 'push', '-m', 'mekong-optimize-auto']);
  }
  
  async stashPop(): Promise<void> {
    await this.execGit(['stash', 'pop']);
  }
  
  async getCurrentBranch(): Promise<string> {
    const result = await this.execGit(['rev-parse', '--abbrev-ref', 'HEAD']);
    return result.trim();
  }
  
  async hasUncommittedChanges(): Promise<boolean> {
    const result = await this.execGit(['status', '--porcelain']);
    return result.trim().length > 0;
  }
  
  async resetHard(ref = 'HEAD'): Promise<void> {
    await this.execGit(['reset', '--hard', ref]);
  }
  
  async getLastCommitMessage(): Promise<string> {
    const result = await this.execGit(['log', '-1', '--pretty=%B']);
    return result.trim();
  }
  
  execGit(args: string[]): Promise<string> {
    return new Promise((resolve, reject) => {
      const child = spawn('git', args, {
        cwd: this.cwd,
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout?.on('data', (data) => {
        stdout += data.toString();
      });
      
      child.stderr?.on('data', (data) => {
        stderr += data.toString();
      });
      
      child.on('close', (code) => {
        if (code === 0) {
          resolve(stdout);
        } else {
          reject(new Error(`Git failed: ${stderr || stdout}`));
        }
      });
    });
  }
}
