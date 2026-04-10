// Mock data for tool execution panel — replaced by API in Phase 7

import type { ToolDef, ToolCall } from "@/lib/tool-types";

export const MOCK_TOOLS: ToolDef[] = [
  // Read tools
  { id: "read_file", name: "Read", description: "Read file contents", category: "read", hotkey: "R" },
  { id: "glob", name: "Glob", description: "Pattern match file paths", category: "read", hotkey: "G" },
  { id: "grep", name: "Grep", description: "Search file contents with regex", category: "read", hotkey: "F" },
  { id: "ls", name: "LS", description: "List directory contents", category: "read" },
  // Write tools
  { id: "write_file", name: "Write", description: "Create or overwrite a file", category: "write", hotkey: "W", approvalRequired: true },
  { id: "edit_file", name: "Edit", description: "Apply targeted string replacements", category: "write", hotkey: "E" },
  { id: "notebook_edit", name: "NotebookEdit", description: "Modify Jupyter notebook cells", category: "write" },
  // Execute tools
  { id: "bash", name: "Bash", description: "Run shell commands", category: "execute", hotkey: "B", approvalRequired: true },
  { id: "web_fetch", name: "WebFetch", description: "Fetch and analyze web pages", category: "execute" },
  { id: "web_search", name: "WebSearch", description: "Search the web for information", category: "execute", hotkey: "S" },
  // Meta tools
  { id: "todo_write", name: "TodoWrite", description: "Update task checklist", category: "meta" },
  { id: "task", name: "Task", description: "Spawn sub-agent for parallel work", category: "meta", hotkey: "T" },
  // Blocked tools
  { id: "rm_rf", name: "rm -rf", description: "Destructive delete — blocked by policy", category: "blocked" },
  { id: "git_force", name: "git push --force", description: "Force push — blocked by policy", category: "blocked" },
];

export const MOCK_TOOL_CALLS: ToolCall[] = [
  {
    id: "tc1",
    toolId: "read_file",
    toolName: "Read",
    args: { file_path: "src/auth/user-service.ts" },
    status: "complete",
    result: "247 lines read",
    durationMs: 12,
    timestamp: Date.now() - 85_000,
  },
  {
    id: "tc2",
    toolId: "grep",
    toolName: "Grep",
    args: { pattern: "JWT", path: "src/auth/" },
    status: "complete",
    result: "8 matches found",
    durationMs: 34,
    timestamp: Date.now() - 82_000,
  },
  {
    id: "tc3",
    toolId: "edit_file",
    toolName: "Edit",
    args: { file_path: "src/auth/user-service.ts" },
    status: "running",
    timestamp: Date.now() - 5_000,
  },
];
