/**
 * Skill Loader - Loads and manages skills for both personas
 */

import * as fs from 'fs';
import * as path from 'path';
import { ConfigManager } from './config-manager';

export interface SkillDefinition {
  name: string;
  description: string;
  version: string;
  author?: string;
  tags?: string[];
  entryPoint: string;
  commands?: SkillCommand[];
  hooks?: SkillHook[];
  config?: Record<string, any>;
}

export interface SkillCommand {
  name: string;
  description: string;
  usage: string;
  handler: string;
}

export interface SkillHook {
  event: string;
  matcher: string;
  command: string;
  persona?: 'mekong' | 'agentkit' | 'both';
}

export class SkillLoader {
  private configRoot: string;
  private configManager: ConfigManager;
  private skills: Map<string, SkillDefinition> = new Map();
  private skillsDir: string;

  constructor(configRoot: string, configManager: ConfigManager) {
    this.configRoot = configRoot;
    this.configManager = configManager;
    this.skillsDir = path.join(configRoot, '.claude', 'skills');
  }

  async loadAll(): Promise<void> {
    if (!fs.existsSync(this.skillsDir)) {
      console.log('[SkillLoader] No skills directory found');
      return;
    }

    const skillDirs = fs.readdirSync(this.skillsDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name);

    for (const skillDir of skillDirs) {
      await this.loadSkill(skillDir);
    }

    console.log(`[SkillLoader] Loaded ${this.skills.size} skills`);
  }

  private async loadSkill(skillDir: string): Promise<void> {
    const skillPath = path.join(this.skillsDir, skillDir);
    const skillMdPath = path.join(skillPath, 'SKILL.md');
    const skillJsonPath = path.join(skillPath, 'skill.json');

    let skill: SkillDefinition | null = null;

    if (fs.existsSync(skillMdPath)) {
      skill = this.parseSkillMd(skillMdPath, skillDir);
    } else if (fs.existsSync(skillJsonPath)) {
      const parsed = JSON.parse(fs.readFileSync(skillJsonPath, 'utf-8'));
      skill = { ...parsed, entryPoint: skillPath };
    }

    if (skill) {
      this.skills.set(skill.name, skill);
    }
  }

  private parseSkillMd(filePath: string, dirName: string): SkillDefinition | null {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const match = content.match(/^---\n([\s\S]*?)\n---/);
      if (!match) return null;

      const frontmatter = match[1] || '';
      const parseField = (field: string) => {
        const regex = new RegExp(`${field}:\\s*(.+)`);
        const m = frontmatter.match(regex);
        return m ? m[1].trim() : undefined;
      };

      const name = parseField('name') || dirName;
      const description = parseField('description') || '';
      const version = parseField('version') || '1.0.0';
      const author = parseField('author');
      const tagsStr = parseField('tags');
      const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()) : [];

      return {
        name,
        description,
        version,
        author,
        tags,
        entryPoint: path.dirname(filePath),
      };
    } catch (error) {
      console.error(`[SkillLoader] Failed to parse ${filePath}:`, error);
      return null;
    }
  }

  getSkill(name: string): SkillDefinition | undefined {
    return this.skills.get(name);
  }

  getAllSkills(): SkillDefinition[] {
    return Array.from(this.skills.values());
  }

  getSkillsByTag(tag: string): SkillDefinition[] {
    return Array.from(this.skills.values()).filter(s => s.tags?.includes(tag));
  }

  isLoaded(name: string): boolean {
    return this.skills.has(name);
  }
}
