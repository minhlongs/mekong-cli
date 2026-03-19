import { writeFileSync } from 'node:fs';
import { randomUUID } from 'node:crypto';

export interface Lesson {
  id: string;
  task: string;
  result: string;
  lesson: string;
  tags: string[];
  timestamp: Date;
  success: boolean;
}

export interface LessonFilter {
  tags?: string[];
  success?: boolean;
  since?: Date;
}

const store: Lesson[] = [];

export function recordLesson(lesson: Lesson): void {
  store.push({ ...lesson });
}

export function getLessons(filter?: LessonFilter): Lesson[] {
  if (!filter) return [...store];

  return store.filter((l) => {
    if (filter.success !== undefined && l.success !== filter.success) return false;
    if (filter.since && l.timestamp < filter.since) return false;
    if (filter.tags && filter.tags.length > 0) {
      const hasTag = filter.tags.some((t) => l.tags.includes(t));
      if (!hasTag) return false;
    }
    return true;
  });
}

function extractTags(text: string): string[] {
  const words = text.toLowerCase().match(/\b[a-z][a-z0-9-]{2,}\b/g) ?? [];
  const stopWords = new Set(['the', 'and', 'for', 'are', 'was', 'not', 'has', 'with', 'this', 'that']);
  return [...new Set(words.filter((w) => !stopWords.has(w)))].slice(0, 8);
}

function summarizeLesson(task: string, result: string, success: boolean): string {
  if (success) {
    return `Task succeeded: "${task.slice(0, 80)}". Key outcome: ${result.slice(0, 120)}.`;
  }
  return `Task failed: "${task.slice(0, 80)}". Failure: ${result.slice(0, 120)}. Avoid repeating this pattern.`;
}

export function extractLessonFromTask(task: string, result: string, success: boolean): Lesson {
  const tags = [...extractTags(task), ...extractTags(result)].slice(0, 10);
  return {
    id: randomUUID(),
    task,
    result,
    lesson: summarizeLesson(task, result, success),
    tags,
    timestamp: new Date(),
    success,
  };
}

export function getRelevantKnowledge(task: string): Lesson[] {
  const keywords = extractTags(task);
  if (keywords.length === 0) return [];

  return store
    .filter((l) => keywords.some((kw) => l.tags.includes(kw) || l.task.toLowerCase().includes(kw)))
    .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
    .slice(0, 10);
}

export function exportLessons(outputPath: string): void {
  const payload = JSON.stringify(store, null, 2);
  writeFileSync(outputPath, payload, 'utf-8');
}
