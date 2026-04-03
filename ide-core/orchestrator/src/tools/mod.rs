use anyhow::Result;
use serde_json::Value;

use crate::types::{FunctionDef, ToolDef};

pub mod ask_user;
pub mod bash_tool;
pub mod file_edit;
pub mod file_read;
pub mod file_write;
pub mod glob_tool;
pub mod grep_tool;
pub mod list_dir;
pub mod mekong_project;
pub mod web_fetch;

/// Permission level required to execute a tool
#[derive(Debug, Clone, PartialEq)]
pub enum PermissionLevel {
    ReadOnly,
    WriteFile,
    Execute,
    Dangerous,
}

/// Result from a tool execution
#[derive(Debug, Clone)]
pub struct ToolResult {
    pub content: String,
    pub is_error: bool,
    pub truncated: bool,
}

/// Every tool implements this trait
#[async_trait::async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    fn parameters(&self) -> Value;
    fn permission_level(&self) -> PermissionLevel;
    async fn execute(&self, args: Value) -> Result<ToolResult>;
}

/// Validate that a path resolves within the current working directory (workspace root).
/// Prevents path traversal attacks (e.g. `../../etc/passwd`).
///
/// For new files, the parent directory is used for validation.
/// Returns the original path as a PathBuf on success.
pub fn validate_workspace_path(path: &str) -> Result<std::path::PathBuf, String> {
    let p = std::path::Path::new(path);
    let parent = p.parent().unwrap_or(std::path::Path::new("."));

    // If parent doesn't exist yet (new file to be created), check the nearest ancestor
    let canonical_parent = {
        let mut check = parent.to_path_buf();
        loop {
            match std::fs::canonicalize(&check) {
                Ok(c) => break c,
                Err(_) => {
                    if let Some(up) = check.parent() {
                        check = up.to_path_buf();
                    } else {
                        return Err(format!("Cannot resolve any ancestor of path: {path}"));
                    }
                }
            }
        }
    };

    let cwd = std::env::current_dir().map_err(|e| format!("Cannot get cwd: {e}"))?;

    if !canonical_parent.starts_with(&cwd) {
        return Err(format!(
            "Path escapes workspace boundary: {path} (resolved: {})",
            canonical_parent.display()
        ));
    }

    Ok(std::path::PathBuf::from(path))
}

/// Convert a Tool to an OpenAI-compatible function definition
pub fn tool_to_def(tool: &dyn Tool) -> ToolDef {
    ToolDef {
        tool_type: "function".to_string(),
        function: FunctionDef {
            name: tool.name().to_string(),
            description: tool.description().to_string(),
            parameters: tool.parameters(),
        },
    }
}

/// Registry holding all available tools
pub struct ToolRegistry {
    tools: Vec<Box<dyn Tool>>,
    workspace: String,
}

impl ToolRegistry {
    pub fn new(workspace: &str) -> Self {
        let ws = workspace.to_string();
        let tools: Vec<Box<dyn Tool>> = vec![
            Box::new(file_read::FileReadTool),
            Box::new(file_write::FileWriteTool),
            Box::new(file_edit::FileEditTool),
            Box::new(bash_tool::BashTool::new()),
            Box::new(glob_tool::GlobTool),
            Box::new(grep_tool::GrepTool),
            Box::new(web_fetch::WebFetchTool),
            Box::new(ask_user::AskUserTool),
            Box::new(list_dir::ListDirTool),
            Box::new(mekong_project::MekongProjectTool::new(&ws)),
        ];
        Self {
            tools,
            workspace: ws,
        }
    }

    /// Get all tool definitions for sending to the LLM
    pub fn all_tool_defs(&self) -> Vec<ToolDef> {
        self.tools.iter().map(|t| tool_to_def(t.as_ref())).collect()
    }

    /// Execute a tool by name
    pub async fn execute(&self, name: &str, args: Value) -> Result<ToolResult> {
        let tool = self
            .tools
            .iter()
            .find(|t| t.name() == name)
            .ok_or_else(|| anyhow::anyhow!("Unknown tool: {name}"))?;
        tool.execute(args).await
    }

    /// Get permission level for a tool
    pub fn permission_level(&self, name: &str) -> Option<PermissionLevel> {
        self.tools
            .iter()
            .find(|t| t.name() == name)
            .map(|t| t.permission_level())
    }

    /// Read MEKONG.md project file if it exists
    pub fn read_project_file(&self) -> Option<String> {
        crate::project::load_project_context(&self.workspace)
    }
}
