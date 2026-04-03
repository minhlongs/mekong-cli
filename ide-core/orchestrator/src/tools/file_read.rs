use anyhow::Result;
use serde_json::Value;

use super::{PermissionLevel, ToolResult};

const MAX_OUTPUT_CHARS: usize = 30_000;

pub struct FileReadTool;

#[async_trait::async_trait]
impl super::Tool for FileReadTool {
    fn name(&self) -> &str {
        "file_read"
    }

    fn description(&self) -> &str {
        "Read a file's contents. Returns line-numbered output. Supports optional line range."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
                "start_line": {"type": "integer", "description": "Start line (1-based, optional)"},
                "end_line": {"type": "integer", "description": "End line (inclusive, optional)"}
            },
            "required": ["path"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let path = args["path"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'path' parameter"))?;

        // Path traversal protection
        if let Err(reason) = super::validate_workspace_path(path) {
            return Ok(ToolResult {
                content: format!("Access denied: {reason}"),
                is_error: true,
                truncated: false,
            });
        }

        let content = match tokio::fs::read(path).await {
            Ok(bytes) => bytes,
            Err(e) => {
                return Ok(ToolResult {
                    content: format!("Error reading {path}: {e}"),
                    is_error: true,
                    truncated: false,
                });
            }
        };

        // Binary detection: check first 1KB for null bytes
        let check_len = content.len().min(1024);
        if content[..check_len].contains(&0) {
            return Ok(ToolResult {
                content: format!("{path}: binary file ({} bytes)", content.len()),
                is_error: false,
                truncated: false,
            });
        }

        let text = String::from_utf8_lossy(&content);
        let lines: Vec<&str> = text.lines().collect();
        let total = lines.len();

        let start = args["start_line"]
            .as_u64()
            .map(|n| (n as usize).saturating_sub(1))
            .unwrap_or(0);
        let end = args["end_line"]
            .as_u64()
            .map(|n| n as usize)
            .unwrap_or(total)
            .min(total);

        let numbered: String = lines[start..end]
            .iter()
            .enumerate()
            .map(|(i, line)| format!("{:>6}\t{}", start + i + 1, line))
            .collect::<Vec<_>>()
            .join("\n");

        let truncated = numbered.chars().count() > MAX_OUTPUT_CHARS;
        let output = if truncated {
            // Use char boundary slicing to avoid splitting UTF-8 sequences
            let safe_head: String = numbered.chars().take(MAX_OUTPUT_CHARS).collect();
            format!(
                "{safe_head}\n\n[... truncated, showing {}/{} lines ...]",
                end - start,
                total
            )
        } else {
            numbered
        };

        Ok(ToolResult {
            content: output,
            is_error: false,
            truncated,
        })
    }
}
