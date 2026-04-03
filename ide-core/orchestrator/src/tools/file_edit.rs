use anyhow::Result;
use serde_json::Value;

use super::{PermissionLevel, ToolResult};

pub struct FileEditTool;

#[async_trait::async_trait]
impl super::Tool for FileEditTool {
    fn name(&self) -> &str {
        "file_edit"
    }

    fn description(&self) -> &str {
        "Edit a file by replacing an exact string match. old_str must appear exactly once in the file."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to edit"},
                "old_str": {"type": "string", "description": "Exact string to find (must appear once)"},
                "new_str": {"type": "string", "description": "Replacement string"}
            },
            "required": ["path", "old_str", "new_str"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::WriteFile
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'path' parameter"))?;
        let old_str = args["old_str"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'old_str' parameter"))?;
        let new_str = args["new_str"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'new_str' parameter"))?;

        // Path traversal protection
        if let Err(reason) = super::validate_workspace_path(path) {
            return Ok(ToolResult {
                content: format!("Access denied: {reason}"),
                is_error: true,
                truncated: false,
            });
        }

        let content = match tokio::fs::read_to_string(path).await {
            Ok(c) => c,
            Err(e) => {
                return Ok(ToolResult {
                    content: format!("Error reading {path}: {e}"),
                    is_error: true,
                    truncated: false,
                });
            }
        };

        let count = content.matches(old_str).count();
        if count == 0 {
            // Find similar strings for helpful error
            let first_line = old_str.lines().next().unwrap_or(old_str);
            let short = &first_line[..first_line.len().min(40)];
            let similar: Vec<&str> = content
                .lines()
                .filter(|l| l.contains(&short[..short.len().min(20)]))
                .take(3)
                .collect();
            let hint = if similar.is_empty() {
                String::new()
            } else {
                format!("\nSimilar lines found:\n{}", similar.join("\n"))
            };
            return Ok(ToolResult {
                content: format!("old_str not found in {path}.{hint}"),
                is_error: true,
                truncated: false,
            });
        }
        if count > 1 {
            return Ok(ToolResult {
                content: format!(
                    "old_str appears {count} times in {path}. Must be unique. Add more context."
                ),
                is_error: true,
                truncated: false,
            });
        }

        let new_content = content.replacen(old_str, new_str, 1);
        tokio::fs::write(path, &new_content).await.map_err(|e| {
            anyhow::anyhow!("Failed to write {path}: {e}")
        })?;

        // Show edited region with 3 lines of context
        let new_lines: Vec<&str> = new_content.lines().collect();
        let edit_pos = new_content
            .find(new_str)
            .unwrap_or(0);
        let edit_line = new_content[..edit_pos].lines().count();
        let start = edit_line.saturating_sub(3);
        let end = (edit_line + new_str.lines().count() + 3).min(new_lines.len());

        let context: String = new_lines[start..end]
            .iter()
            .enumerate()
            .map(|(i, line)| format!("{:>6}\t{}", start + i + 1, line))
            .collect::<Vec<_>>()
            .join("\n");

        Ok(ToolResult {
            content: format!("Edited {path}:\n{context}"),
            is_error: false,
            truncated: false,
        })
    }
}
