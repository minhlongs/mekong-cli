/**
 * 🎨 VIBE Flow - Visual Workflow Builder (Proxy)
 */
export * from './src/flow/types';
export * from './src/flow/nodes';
export { VibeFlow } from './src/flow/builder';
export { FlowCopilot } from './src/flow/copilot';

import { VibeFlow } from './src/flow/builder';

/** @deprecated Use src/flow modules directly */
export const vibeFlow = new VibeFlow();
export const flowCopilot = vibeFlow; // Compatibility alias

export default { vibeFlow, VibeFlow };
