/**
 * Public API layer barrel — re-exports all endpoint modules and shared types.
 */

export * from "./api-types";
export * from "./api-config";
export { apiClient } from "./api-client";
export { isApiReachable, resetReachabilityCache, withDemoFallback } from "./demo-mode";

// Endpoint groups
export * as agentApi from "./endpoints/agent-api";
export * as engineApi from "./endpoints/engine-api";
export * as toolApi from "./endpoints/tool-api";
export * as taskApi from "./endpoints/task-api";
export * as tradingApi from "./endpoints/trading-api";
export * as contextApi from "./endpoints/context-api";
