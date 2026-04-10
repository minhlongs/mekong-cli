import { IdeShell } from "@/components/layout";

/**
 * Mekong IDE workspace — Phase 2: three-panel shell.
 * IdeShell provides: LeftSidebar | CenterPanel (tabs+editor+terminal) | RightPanel (agent chat).
 */
export default function IdePage() {
  return <IdeShell />;
}
