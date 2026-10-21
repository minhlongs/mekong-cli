/**
 * Tests for mekong cook command — platform filtering
 */

import { describe, it, expect, vi } from 'vitest';

vi.mock('../../../../plugins/mekong-tasks/recipe-loader.js', () => ({
  loadAllRecipes: vi.fn().mockReturnValue([]),
  loadRecipe: vi.fn(),
  runRecipe: vi.fn(),
}));
vi.mock('../../../plugins/mekong-tasks/recipe-loader.js', () => ({
  loadAllRecipes: vi.fn().mockReturnValue([]),
  loadRecipe: vi.fn(),
  runRecipe: vi.fn(),
}));

import { filterRecipesByPlatform, formatCookSummary, type Recipe } from '../../src/recipe-runner.js';

// Mock recipes for testing (simplified shape)
const mockRecipes = [
  {
    name: 'Cloudflare Deploy',
    platforms: ['cloudflare'],
  },
  {
    name: 'General Setup',
    platforms: ['general'],
  },
  {
    name: 'Multi-platform Build',
    platforms: ['cloudflare', 'vercel'],
  },
  {
    name: 'No Platform Specified',
    // platforms undefined
  },
] as unknown as Recipe[];

describe('Platform Filtering', () => {
  describe('filterRecipesByPlatform', () => {
    it('should filter cloudflare recipes', () => {
      const filtered = filterRecipesByPlatform(mockRecipes, 'cloudflare');
      expect(filtered.length).toBe(2);
      expect(filtered.map(r => r.name)).toContain('Cloudflare Deploy');
      expect(filtered.map(r => r.name)).toContain('Multi-platform Build');
    });

    it('should filter general recipes only', () => {
      const filtered = filterRecipesByPlatform(mockRecipes, 'general');
      expect(filtered.length).toBe(2);
      expect(filtered.map(r => r.name)).toContain('General Setup');
      expect(filtered.map(r => r.name)).toContain('No Platform Specified');
    });

    it('should filter vercel recipes', () => {
      const filtered = filterRecipesByPlatform(mockRecipes, 'vercel');
      expect(filtered.length).toBe(1);
      expect(filtered[0].name).toBe('Multi-platform Build');
    });

    it('should return empty for unknown platform', () => {
      const filtered = filterRecipesByPlatform(mockRecipes, 'netlify');
      expect(filtered.length).toBe(0);
    });
  });
});

describe('formatCookSummary', () => {
  it('should format summary correctly', () => {
    const summary = {
      total: 10,
      matched: 3,
      skipped: 7,
      results: [
        {
          recipeName: 'Recipe 1',
          status: 'success' as const,
          stepsCompleted: 5,
          stepsFailed: 0,
          output: 'Output 1',
        },
        {
          recipeName: 'Recipe 2',
          status: 'failed' as const,
          stepsCompleted: 2,
          stepsFailed: 3,
          error: 'Something failed',
        },
      ],
    };

    const formatted = formatCookSummary(summary);
    expect(formatted).toContain('Total recipes: 10');
    expect(formatted).toContain('Matched: 3');
    expect(formatted).toContain('Skipped: 7');
    expect(formatted).toContain('✓ Recipe 1');
    expect(formatted).toContain('✗ Recipe 2');
  });

  it('should handle empty results', () => {
    const summary = {
      total: 5,
      matched: 0,
      skipped: 5,
      results: [],
    };
    const formatted = formatCookSummary(summary);
    expect(formatted).toContain('Total recipes: 5');
    expect(formatted).toContain('Matched: 0');
    expect(formatted).toContain('Skipped: 5');
  });
});
