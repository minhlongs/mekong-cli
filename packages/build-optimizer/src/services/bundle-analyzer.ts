import { readFile } from 'fs/promises';
import { join } from 'path';
import { stat } from 'fs/promises';
import { BundleMetrics, AssetMetrics } from '../types/index.js';

interface BundleStatsOptions {
  outputDir: string;
  statsFile?: string;
}

export class BundleAnalyzer {
  async analyze(options: BundleStatsOptions): Promise<BundleMetrics> {
    const { outputDir, statsFile = 'stats.json' } = options;
    
    // Try to load stats.json if available (webpack/vite-bundle-analyzer)
    const statsPath = join(outputDir, statsFile);
    
    try {
      const statsContent = await readFile(statsPath, 'utf-8');
      const stats = JSON.parse(statsContent);
      return this.parseStatsJson(stats, outputDir);
    } catch {
      // Fallback to directory analysis
      return this.analyzeDirectory(outputDir);
    }
  }
  
  private parseStatsJson(stats: unknown, outputDir: string): BundleMetrics {
    const assets: AssetMetrics[] = [];
    const chunks: string[] = [];
    let totalSize = 0;
    let gzipSize = 0;
    
    // Handle webpack stats format
    if (stats && typeof stats === 'object') {
      const s = stats as Record<string, unknown>;
      
      // Parse assets
      if (Array.isArray(s.assets)) {
        for (const asset of s.assets) {
          if (asset && typeof asset === 'object') {
            const a = asset as Record<string, unknown>;
            const size = typeof a.size === 'number' ? a.size : 0;
            const name = String(a.name || 'unknown');
            
            assets.push({
              name,
              size,
              gzipSize: typeof a.gzipSize === 'number' ? a.gzipSize : size,
              type: this.getAssetType(name),
            });
            
            totalSize += size;
          }
        }
      }
      
      // Parse chunks
      if (Array.isArray(s.chunks)) {
        for (const chunk of s.chunks) {
          if (chunk && typeof chunk === 'object') {
            const c = chunk as Record<string, unknown>;
            if (c.names && Array.isArray(c.names)) {
              chunks.push(...c.names.filter((n): n is string => typeof n === 'string'));
            }
          }
        }
      }
    }
    
    return {
      totalSize,
      gzipSize,
      assets,
      chunks,
    };
  }
  
  private async analyzeDirectory(outputDir: string): Promise<BundleMetrics> {
    const assets: AssetMetrics[] = [];
    const chunks: string[] = [];
    let totalSize = 0;
    let gzipSize = 0;
    
    // Fallback: analyze output directory
    try {
      const files = await this.getAllFiles(outputDir);
      
      for (const file of files) {
        const { size } = await stat(file);
        const relativePath = file.replace(outputDir, '');
        
        assets.push({
          name: relativePath,
          size,
          gzipSize: size, // Approximation without actual gzip
          type: this.getAssetType(relativePath),
        });
        
        totalSize += size;
        gzipSize += size * 0.3; // Rough estimate: gzip ~30% of original
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
    }
    
    return {
      totalSize,
      gzipSize,
      assets,
      chunks,
    };
  }
  
  private async getAllFiles(dir: string): Promise<string[]> {
    const { readdir } = await import('fs/promises');
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
    } catch {
      // Directory doesn't exist
    }
    
    return files;
  }
  
  private getAssetType(filename: string): AssetMetrics['type'] {
    if (filename.endsWith('.js') || filename.endsWith('.mjs')) return 'js';
    if (filename.endsWith('.css')) return 'css';
    if (/\.(png|jpg|jpeg|gif|svg|webp)$/.test(filename)) return 'image';
    if (/\.(woff|woff2|ttf|otf|eot)$/.test(filename)) return 'font';
    return 'other';
  }
  
  calculateBundleBreakdown(metrics: BundleMetrics): Record<string, number> {
    const breakdown: Record<string, number> = {
      js: 0,
      css: 0,
      image: 0,
      font: 0,
      other: 0,
    };
    
    for (const asset of metrics.assets) {
      breakdown[asset.type] += asset.size;
    }
    
    return breakdown;
  }
  
  findLargestAssets(metrics: BundleMetrics, limit = 10): AssetMetrics[] {
    return [...metrics.assets]
      .sort((a, b) => b.size - a.size)
      .slice(0, limit);
  }
}
