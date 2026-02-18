import * as fs from 'fs/promises';
import * as path from 'path';
import { PackageInfo, DependencyGraph } from './types';

export class MonorepoIndexer {
  private rootDir: string;

  constructor(rootDir: string) {
    this.rootDir = path.resolve(rootDir);
  }

  async scan(): Promise<DependencyGraph> {
    const nodes: Record<string, PackageInfo> = {};
    const edges: Array<{ from: string; to: string; type: 'prod' | 'dev' | 'peer' }> = [];

    // Find all package.json files
    const packageFiles = await this.findPackageJsonFiles(this.rootDir);

    for (const pkgPath of packageFiles) {
      try {
        const content = await fs.readFile(pkgPath, 'utf-8');
        const pkg = JSON.parse(content);
        
        // Skip root package if it doesn't have a name or is just a workspace root container without meaningful code
        if (!pkg.name) continue;

        nodes[pkg.name] = {
          name: pkg.name,
          version: pkg.version || '0.0.0',
          path: path.dirname(pkgPath),
          private: pkg.private,
          dependencies: pkg.dependencies,
          devDependencies: pkg.devDependencies,
          peerDependencies: pkg.peerDependencies,
          workspaces: pkg.workspaces,
        };
      } catch (error) {
        console.warn(`Failed to parse ${pkgPath}: ${error}`);
      }
    }

    // Build edges
    for (const [name, info] of Object.entries(nodes)) {
      if (info.dependencies) {
        for (const dep of Object.keys(info.dependencies)) {
          if (nodes[dep]) {
            edges.push({ from: name, to: dep, type: 'prod' });
          }
        }
      }
      if (info.devDependencies) {
        for (const dep of Object.keys(info.devDependencies)) {
          if (nodes[dep]) {
            edges.push({ from: name, to: dep, type: 'dev' });
          }
        }
      }
      if (info.peerDependencies) {
        for (const dep of Object.keys(info.peerDependencies)) {
          if (nodes[dep]) {
            edges.push({ from: name, to: dep, type: 'peer' });
          }
        }
      }
    }

    return { nodes, edges };
  }

  private async findPackageJsonFiles(dir: string, ig = new Set(['node_modules', '.git', 'dist', 'build', '.next'])): Promise<string[]> {
    let results: string[] = [];
    
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          if (!ig.has(entry.name)) {
            results = results.concat(await this.findPackageJsonFiles(fullPath, ig));
          }
        } else if (entry.name === 'package.json') {
          results.push(fullPath);
        }
      }
    } catch (error) {
      // Ignore access errors
    }
    
    return results;
  }
}
