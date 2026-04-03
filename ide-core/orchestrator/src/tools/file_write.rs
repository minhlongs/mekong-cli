use anyhow::Result;
use serde_json::Value;
use std::path::Path;

use super::{PermissionLevel, ToolResult};

pub struct FileWriteTool;

#[async_trait::async_trait]
impl super::Tool for FileWriteTool {
    fn name(&self) -> &str {
        "file_write"
    }

    fn description(&self) -> &str {
        "Create or overwrite a file with the given content. Creates parent directories if needed."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::WriteFile
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'path' parameter"))?;
        let content = args["content"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'content' parameter"))?;

        // Path traversal protection
        if let Err(reason) = super::validate_workspace_path(path) {
            return Ok(ToolResult {
                content: format!("Access denied: {reason}"),
                is_error: true,
                truncated: false,
            });
        }

        // Create parent directories
        if let Some(parent) = Path::new(path).parent() {
            if !parent.exists() {
                tokio::fs::create_dir_all(parent).await.map_err(|e| {
                    anyhow::anyhow!("Failed to create directory {}: {e}", parent.display())
                })?;
            }
        }

        tokio::fs::write(path, content).await.map_err(|e| {
            anyhow::anyhow!("Failed to write {path}: {e}")
        })?;

        let size = content.len();
        Ok(ToolResult {
            content: format!("Wrote {size} bytes to {path}"),
            is_error: false,
            truncated: false,
        })
    }
}
