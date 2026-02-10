import { spawn } from 'child_process';
import { stat, readdir } from 'fs/promises';
import { join } from 'path';
import { createReadStream } from 'fs';
import { createGzip } from 'zlib';
import { pipeline } from 'stream/promises';
import { BuildMetrics, AssetMetrics, AppConfig } from '../types/index.js';
import { BuildError } from '../utils/errors.js';

interface BuildOptions {
  app: AppConfig;
  cwd: string;
}

export class BuildService {
  async build(options: BuildOptions): Promise<BuildMetrics> {
    const { app, cwd } = options;
    const startTime = Date.now();
    
    try {
      await this.runBuildCommand(app.buildCommand, cwd);
      const duration = Date.now() - startTime;
      
      const outputPath = join(cwd, app.outputDir);
      const assets = await this.analyzeAssets(outputPath);
      const bundleSize = assets.reduce((sum, a) => sum + a.size, 0);
      
      return {
        appName: app.name,
        duration,
        bundleSize,
        assets,
        timestamp: new Date(),
        success: true,
      };
    } catch (error) {
      throw new BuildError(
        `Build failed for ${app.name}`,
        { app: app.name, error: String(error) }
      );
    }
  }
  
  private runBuildCommand(command: string, cwd: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const [cmd, ...args] = command.split(' ');
      const child = spawn(cmd, args, {
        cwd,
        stdio: 'pipe',
        shell: true,
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
          resolve();
        } else {
          reject(new Error(`Build exited with code ${code}: ${stderr || stdout}`));
        }
      });
    });
  }
  
  private async analyzeAssets(dir: string): Promise<AssetMetrics[]> {
    const assets: AssetMetrics[] = [];
    
    try {
      const files = await this.getAllFiles(dir);
      
      for (const file of files) {
        const size = (await stat(file)).size;
        const gzipSize = await this.calculateGzipSize(file);
        
        assets.push({
          name: file.replace(dir, ''),
          size,
          gzipSize,
          type: this.getAssetType(file),
        });
      }
    } catch (error) {
      // Output dir might not exist yet
    }
    
    return assets;
  }
  
  private async getAllFiles(dir: string): Promise<string[]> {
    const files: string[] = [];
    
    try {
      const entries = await readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const path = join(dir, entry.name);
        if (entry.isDirectory()) {
          files.push(...await this.getAllFiles(path));
        } else {
          files.push(path);
        }
      }
    } catch (error) {
      // Directory doesn't exist
    }
    
    return files;
  }
  
  private async calculateGzipSize(filePath: string): Promise<number> {
    try {
      const chunks: Buffer[] = [];
      const gzip = createGzip();
      const readStream = createReadStream(filePath);
      
      readStream.pipe(gzip);
      
      return new Promise((resolve, reject) => {
        gzip.on('data', (chunk) => chunks.push(chunk));
        gzip.on('end', () => {
          const totalSize = Buffer.concat(chunks).length;
          resolve(totalSize);
        });
        gzip.on('error', reject);
        readStream.on('error', reject);
      });
    } catch {
      // Fallback to actual size if gzip fails
      const { size } = await stat(filePath);
      return size;
    }
  }
  
  private getAssetType(filename: string): AssetMetrics['type'] {
    if (filename.endsWith('.js') || filename.endsWith('.mjs') || filename.endsWith('.cjs')) return 'js';
    if (filename.endsWith('.css')) return 'css';
    if (/\.(png|jpg|jpeg|gif|svg|webp|ico)$/.test(filename)) return 'image';
    if (/\.(woff|woff2|ttf|otf|eot)$/.test(filename)) return 'font';
    return 'other';
  }
}
