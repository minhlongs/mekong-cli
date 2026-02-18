import * as fs from 'fs/promises';
import * as path from 'path';
import { HealthStatus } from './types';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export interface ProjectHealth {
  name: string;
  path: string;
  isBuilt: boolean;
  dependenciesInstalled: boolean;
  techDebt: {
    tsIgnoreCount: number;
    anyCount: number;
    todoCount: number;
  };
  lastBuildTime?: number;
}

export class HealthMonitor {
  private logDir: string;
  private pidFile: string;

  constructor(logDir: string, pidFile: string) {
    this.logDir = logDir;
    this.pidFile = pidFile;
  }

  async checkOpenClawStatus(): Promise<HealthStatus> {
    const status: HealthStatus = {
      service: 'openclaw-worker',
      status: 'down',
      timestamp: Date.now(),
      details: {}
    };

    try {
      // Check PID
      const pid = await fs.readFile(this.pidFile, 'utf-8');
      const isRunning = await this.checkPid(parseInt(pid.trim()));
      
      if (isRunning) {
        status.status = 'healthy';
        status.details!.pid = pid.trim();
      }
    } catch (e) {
      status.details!.pidError = (e as Error).message;
    }

    // Check Logs
    try {
      const logPath = path.join(this.logDir, 'tom_hum.log');
      try {
        const stats = await fs.stat(logPath);
        const lastModified = stats.mtimeMs;
        const timeSinceLastLog = Date.now() - lastModified;

        status.details!.lastLogTime = lastModified;
        status.details!.timeSinceLastLogMs = timeSinceLastLog;

        // If running but no logs for > 5 mins, maybe degraded
        if (status.status === 'healthy' && timeSinceLastLog > 5 * 60 * 1000) {
          status.status = 'degraded';
          status.details!.reason = 'No recent logs';
        }
      } catch (e) {
         status.details!.logMessage = "Log file not found";
      }
    } catch (e) {
      status.details!.logError = (e as Error).message;
    }

    return status;
  }

  async checkProjectHealth(projectPath: string): Promise<ProjectHealth> {
    const pkgJsonPath = path.join(projectPath, 'package.json');
    let name = path.basename(projectPath);
    
    try {
      const pkgContent = await fs.readFile(pkgJsonPath, 'utf-8');
      const pkg = JSON.parse(pkgContent);
      name = pkg.name || name;
    } catch (e) {
      // Not a valid project?
    }

    const nodeModulesPath = path.join(projectPath, 'node_modules');
    const dependenciesInstalled = await this.exists(nodeModulesPath);

    // Check for build artifacts
    const buildDirs = ['dist', 'build', '.next', 'out'];
    let isBuilt = false;
    let lastBuildTime: number | undefined;

    for (const dir of buildDirs) {
      const buildPath = path.join(projectPath, dir);
      if (await this.exists(buildPath)) {
        isBuilt = true;
        try {
            const stats = await fs.stat(buildPath);
            lastBuildTime = stats.mtimeMs;
        } catch {}
        break;
      }
    }
    
    // Check tsconfig.tsbuildinfo if exists
    const tsBuildInfoPath = path.join(projectPath, 'tsconfig.tsbuildinfo');
    if (await this.exists(tsBuildInfoPath)) {
        try {
            const stats = await fs.stat(tsBuildInfoPath);
            lastBuildTime = stats.mtimeMs;
            isBuilt = true; // TS build info implies a build
        } catch {}
    }

    // Quick Tech Debt Scan (grep)
    const techDebt = {
      tsIgnoreCount: 0,
      anyCount: 0,
      todoCount: 0
    };

    try {
       const [tsIgnore, anyType, todo] = await Promise.all([
           this.grepCount(projectPath, "@ts-ignore"),
           this.grepCount(projectPath, ": any"),
           this.grepCount(projectPath, "TODO|FIXME")
       ]);
       
       techDebt.tsIgnoreCount = tsIgnore;
       techDebt.anyCount = anyType;
       techDebt.todoCount = todo;

    } catch (e) {
        // Grep failed or not available
    }

    return {
      name,
      path: projectPath,
      isBuilt,
      dependenciesInstalled,
      techDebt,
      lastBuildTime
    };
  }

  private async exists(path: string): Promise<boolean> {
    try {
      await fs.access(path);
      return true;
    } catch {
      return false;
    }
  }

  private async grepCount(dir: string, pattern: string): Promise<number> {
      try {
          // Use safer excludes compatible with most shells
          // --exclude-dir=DIR is standard in modern grep
          const excludes = [
              '--exclude-dir=node_modules',
              '--exclude-dir=dist',
              '--exclude-dir=.next',
              '--exclude-dir=.git',
              '--exclude-dir=build',
              '--exclude-dir=coverage',
              '--exclude-dir=.turbo'
          ].join(' ');
          
          const includes = [
              '--include="*.ts"',
              '--include="*.tsx"',
              '--include="*.js"',
              '--include="*.jsx"'
          ].join(' ');

          const cmd = `grep -rE "${pattern}" "${dir}" ${excludes} ${includes} | wc -l`;
          const { stdout } = await execAsync(cmd);
          return parseInt(stdout.trim()) || 0;
      } catch (e) {
          return 0;
      }
  }

  private async checkPid(pid: number): Promise<boolean> {
    try {
      process.kill(pid, 0);
      return true;
    } catch (e) {
      return false;
    }
  }
}
