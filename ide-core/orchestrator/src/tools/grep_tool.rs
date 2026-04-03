use anyhow::Result;
use regex::Regex;
use serde_json::Value;
use std::path::Path;
use walkdir::WalkDir;

use super::{PermissionLevel, ToolResult};

const MAX_MATCHES: usize = 100;

pub struct GrepTool;

#[async_trait::async_trait]
impl super::Tool for GrepTool {
    fn name(&self) -> &str {
        "grep"
    }

    fn description(&self) -> &str {
        "Search file contents using regex. Returns file:line:content format. Max 100 matches."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory or file to search (default: .)"},
                "include": {"type": "string", "description": "Glob filter for filenames (e.g. *.rs)"}
            },
            "required": ["pattern"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let pattern_str = args["pattern"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'pattern' parameter"))?;
        let search_path = args["path"].as_str().unwrap_or(".");
        let include = args["include"].as_str();

        let regex = match Regex::new(pattern_str) {
            Ok(r) => r,
            Err(e) => {
                return Ok(ToolResult {
                    content: format!("Invalid regex '{pattern_str}': {e}"),
                    is_error: true,
                    truncated: false,
                });
            }
        };

        let include_glob = include.and_then(|p| glob::Pattern::new(p).ok());

        let root = Path::new(search_path);
        let mut matches = Vec::new();

        let files: Vec<_> = if root.is_file() {
            vec![root.to_path_buf()]
        } else {
            WalkDir::new(root)
                .follow_links(false)
                .into_iter()
                .filter_entry(|e| {
                    let name = e.file_name().to_string_lossy();
                    !matches!(
                        name.as_ref(),
                        ".git" | "node_modules" | "__pycache__" | "target" | ".venv"
                    )
                })
                .filter_map(|e| e.ok())
                .filter(|e| e.file_type().is_file())
                .filter(|e| {
                    if let Some(ref g) = include_glob {
                        g.matches(
                            &e.file_name().to_string_lossy(),
                        )
                    } else {
                        true
                    }
                })
                .map(|e| e.into_path())
                .collect()
        };

        'outer: for file in files {
            let content = match std::fs::read_to_string(&file) {
                Ok(c) => c,
                Err(_) => continue,
            };
            for (i, line) in content.lines().enumerate() {
                if regex.is_match(line) {
                    let display_path = file
                        .strip_prefix(root)
                        .unwrap_or(&file)
                        .to_string_lossy();
                    matches.push(format!("{}:{}:{}", display_path, i + 1, line));
                    if matches.len() >= MAX_MATCHES {
                        break 'outer;
                    }
                }
            }
        }

        let truncated = matches.len() >= MAX_MATCHES;
        let count = matches.len();
        let content = if matches.is_empty() {
            format!("No matches for '{pattern_str}' in {search_path}")
        } else {
            let list = matches.join("\n");
            if truncated {
                format!("{list}\n\n[... truncated at {MAX_MATCHES} matches]")
            } else {
                format!("{list}\n\n({count} matches)")
            }
        };

        Ok(ToolResult {
            content,
            is_error: false,
            truncated,
        })
    }
}
