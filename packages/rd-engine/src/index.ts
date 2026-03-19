// Sources
export { fetchTrendingRepos } from "./sources/github-trending.js";
export type { TrendingRepo } from "./sources/github-trending.js";

export { searchNpmPackages } from "./sources/npm-registry.js";
export type { NpmPackage } from "./sources/npm-registry.js";

export { fetchHNStories } from "./sources/hackernews.js";
export type { HNStory } from "./sources/hackernews.js";

// Core
export { scoreRelevance, filterHighRelevance } from "./analyzer.js";
export type { RdItem } from "./analyzer.js";

export { generateProposal } from "./proposer.js";
export { generateWeeklyReport } from "./reporter.js";
export { RdScheduler } from "./scheduler.js";
