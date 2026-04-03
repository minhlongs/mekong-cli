use anyhow::Result;
use serde_json::Value;
use std::path::PathBuf;

use super::{PermissionLevel, ToolResult};

pub struct MekongProjectTool {
    workspace: PathBuf,
}

impl MekongProjectTool {
    pub fn new(workspace: &str) -> Self {
        Self {
            workspace: PathBuf::from(workspace),
        }
    }
}

#[async_trait::async_trait]
impl super::Tool for MekongProjectTool {
    fn name(&self) -> &str {
        "mekong_project"
    }

    fn description(&self) -> &str {
        "Read MEKONG.md project instructions from the workspace root. Auto-called at session start."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "workspace": {"type": "string", "description": "Workspace root (optional, uses default)"}
            }
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let ws = args["workspace"]
            .as_str()
            .map(PathBuf::from)
            .unwrap_or_else(|| self.workspace.clone());

        let path = ws.join("MEKONG.md");
        match tokio::fs::read_to_string(&path).await {
            Ok(content) => Ok(ToolResult {
                content: format!(
                    "# Project Instructions (MEKONG.md)\n\n{content}"
                ),
                is_error: false,
                truncated: false,
            }),
            Err(_) => {
                // Try CLAUDE.md as fallback
                let claude_path = ws.join("CLAUDE.md");
                match tokio::fs::read_to_string(&claude_path).await {
                    Ok(content) => Ok(ToolResult {
                        content: format!(
                            "# Project Instructions (CLAUDE.md)\n\n{content}"
                        ),
                        is_error: false,
                        truncated: false,
                    }),
                    Err(_) => Ok(ToolResult {
                        content: format!(
                            "No MEKONG.md or CLAUDE.md found in {}",
                            ws.display()
                        ),
                        is_error: false,
                        truncated: false,
                    }),
                }
            }
        }
    }
}
