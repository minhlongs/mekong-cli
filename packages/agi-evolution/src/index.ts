export type { CodebaseAnalysis, RefactoringProposal } from './self-improver.js';
export { analyzeCodebase, generateRefactoringProposals, getQualityScore } from './self-improver.js';

export type { Capability, CapabilityType, CapabilityStats } from './capability-tracker.js';
export { CapabilityRegistry } from './capability-tracker.js';

export type { Lesson, LessonFilter } from './learning-loop.js';
export { recordLesson, getLessons, extractLessonFromTask, getRelevantKnowledge, exportLessons } from './learning-loop.js';

export type { BenchmarkResult, BenchmarkTool, ComparisonReport, ToolSummary } from './benchmark.js';
export { BenchmarkRunner } from './benchmark.js';

export type { VersionReport, BreakingChange } from './version-tracker.js';
export { checkVersions, detectBreakingChanges, generateMigrationGuide } from './version-tracker.js';
