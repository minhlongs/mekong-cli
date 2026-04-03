use anyhow::Result;
use serde_json::Value;
use std::path::Path;
use walkdir::WalkDir;

use super::{PermissionLevel, ToolResult};

const MAX_RESULTS: usize = 1000;

pub struct GlobTool;

#[async_trait::async_trait]
impl super::Tool for GlobTool {
    fn name(&self) -> &str {
        "glob"
    }

    fn description(&self) -> &str {
        "Find files matching a glob pattern (e.g. **/*.rs). Respects .gitignore. Max 1000 results."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.rs, src/**/*.py)"},
                "root": {"type": "string", "description": "Root directory (default: .)"}
            },
            "required": ["pattern"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let pattern = args["pattern"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'pattern' parameter"))?;
        let root = args["root"].as_str().unwrap_or(".");

        let glob_pattern = glob::Pattern::new(pattern).map_err(|e| {
            anyhow::anyhow!("Invalid glob pattern '{pattern}': {e}")
        })?;

        let root_path = Path::new(root);
        let mut matches = Vec::new();

        for entry in WalkDir::new(root_path)
            .follow_links(false)
            .into_iter()
            .filter_entry(|e| {
                let name = e.file_name().to_string_lossy();
                // Skip common ignored directories
                !matches!(
                    name.as_ref(),
                    ".git" | "node_modules" | "__pycache__" | "target" | ".venv"
                )
            })
        {
            let entry = match entry {
                Ok(e) => e,
                Err(_) => continue,
            };
            if !entry.file_type().is_file() {
                continue;
            }
            let rel = entry
                .path()
                .strip_prefix(root_path)
                .unwrap_or(entry.path());
            if glob_pattern.matches_path(rel) {
                matches.push(rel.to_string_lossy().to_string());
                if matches.len() >= MAX_RESULTS {
                    break;
                }
            }
        }

        let truncated = matches.len() >= MAX_RESULTS;
        let count = matches.len();
        let content = if matches.is_empty() {
            format!("No files matching '{pattern}' in {root}")
        } else {
            let list = matches.join("\n");
            if truncated {
                format!("{list}\n\n[... truncated at {MAX_RESULTS} results]")
            } else {
                format!("{list}\n\n({count} files)")
            }
        };

        Ok(ToolResult {
            content,
            is_error: false,
            truncated,
        })
    }
}
