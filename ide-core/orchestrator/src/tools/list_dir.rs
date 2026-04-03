use anyhow::Result;
use serde_json::Value;
use std::path::Path;

use super::{PermissionLevel, ToolResult};

const MAX_ENTRIES: usize = 500;

pub struct ListDirTool;

#[async_trait::async_trait]
impl super::Tool for ListDirTool {
    fn name(&self) -> &str {
        "list_dir"
    }

    fn description(&self) -> &str {
        "List directory contents with type indicators (file/dir/symlink). Max depth 2, max 500 entries."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"},
                "depth": {"type": "integer", "description": "Max depth (default 2)"}
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
        let max_depth = args["depth"].as_u64().unwrap_or(2) as usize;

        let root = Path::new(path);
        if !root.is_dir() {
            return Ok(ToolResult {
                content: format!("{path}: not a directory"),
                is_error: true,
                truncated: false,
            });
        }

        let mut entries = Vec::new();

        for entry in walkdir::WalkDir::new(root)
            .max_depth(max_depth)
            .follow_links(false)
            .sort_by_file_name()
            .into_iter()
            .filter_entry(|e| {
                let name = e.file_name().to_string_lossy();
                !matches!(name.as_ref(), ".git" | "node_modules" | "__pycache__" | "target")
            })
        {
            let entry = match entry {
                Ok(e) => e,
                Err(_) => continue,
            };

            // Skip the root itself
            if entry.path() == root {
                continue;
            }

            let rel = entry
                .path()
                .strip_prefix(root)
                .unwrap_or(entry.path())
                .to_string_lossy();

            let kind = if entry.file_type().is_dir() {
                "dir"
            } else if entry.file_type().is_symlink() {
                "link"
            } else {
                "file"
            };

            entries.push(format!("[{kind}] {rel}"));
            if entries.len() >= MAX_ENTRIES {
                break;
            }
        }

        let truncated = entries.len() >= MAX_ENTRIES;
        let count = entries.len();
        let content = if entries.is_empty() {
            format!("{path}: empty directory")
        } else {
            let list = entries.join("\n");
            if truncated {
                format!("{list}\n\n[... truncated at {MAX_ENTRIES} entries]")
            } else {
                format!("{list}\n\n({count} entries)")
            }
        };

        Ok(ToolResult {
            content,
            is_error: false,
            truncated,
        })
    }
}
