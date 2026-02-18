import { MonorepoIndexer } from './indexer';
import { DependencyGraph } from './types';
import * as path from 'path';

export class ImpactAnalyzer {
  private indexer: MonorepoIndexer;
  private graph: DependencyGraph | null = null;

  constructor(rootDir: string) {
    this.indexer = new MonorepoIndexer(rootDir);
  }

  async analyze(changedFiles: string[]): Promise<string[]> {
    if (!this.graph) {
      this.graph = await this.indexer.scan();
    }

    const impactedPackages = new Set<string>();
    const changedPackages = new Set<string>();

    // 1. Identify which packages contain the changed files
    for (const file of changedFiles) {
      const pkgName = this.findPackageForFile(file);
      if (pkgName) {
        changedPackages.add(pkgName);
        impactedPackages.add(pkgName);
      }
    }

    // 2. Find dependents recursively
    // A change in 'shared' affects 'backend' if 'backend' depends on 'shared'
    // Graph edges: { from: 'backend', to: 'shared' }
    // Reverse lookup needed: who depends on X?
    
    const dependentsMap = this.buildDependentsMap(this.graph);

    const queue = Array.from(changedPackages);
    while (queue.length > 0) {
      const current = queue.shift()!;
      const dependents = dependentsMap.get(current) || [];
      
      for (const dependent of dependents) {
        if (!impactedPackages.has(dependent)) {
          impactedPackages.add(dependent);
          queue.push(dependent);
        }
      }
    }

    return Array.from(impactedPackages);
  }

  private findPackageForFile(filePath: string): string | null {
    if (!this.graph) return null;

    // Sort by path length descending to match longest prefix (deepest nested package) first
    const sortedPackages = Object.values(this.graph.nodes).sort((a, b) => b.path.length - a.path.length);

    for (const pkg of sortedPackages) {
      const relative = path.relative(pkg.path, filePath);
      if (!relative.startsWith('..') && !path.isAbsolute(relative)) {
        return pkg.name;
      }
    }
    return null;
  }

  private buildDependentsMap(graph: DependencyGraph): Map<string, string[]> {
    const map = new Map<string, string[]>();
    
    for (const edge of graph.edges) {
      // edge: from -> to (from depends on to)
      // we want: to -> [from] (who depends on to)
      if (!map.has(edge.to)) {
        map.set(edge.to, []);
      }
      map.get(edge.to)!.push(edge.from);
    }
    
    return map;
  }
}
