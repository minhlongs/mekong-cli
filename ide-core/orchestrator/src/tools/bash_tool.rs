use anyhow::Result;
use regex::Regex;
use serde_json::Value;
use std::time::Duration;
use tokio::process::Command;

use super::{PermissionLevel, ToolResult};
use crate::permissions::get_deny_patterns;

const MAX_OUTPUT_CHARS: usize = 30_000;
const DEFAULT_TIMEOUT_SECS: u64 = 120;

pub struct BashTool {
    deny_patterns: Vec<Regex>,
}

impl BashTool {
    pub fn new() -> Self {
        // Build deny patterns from single source of truth in permissions module
        let deny_patterns: Vec<Regex> = get_deny_patterns()
            .iter()
            .map(|p| Regex::new(p).unwrap())
            .collect();
        Self { deny_patterns }
    }

    fn is_denied(&self, command: &str) -> Option<String> {
        for pattern in &self.deny_patterns {
            if pattern.is_match(command) {
                return Some(format!("Blocked by deny rule: {}", pattern.as_str()));
            }
        }
        None
    }
}

fn truncate_output(output: &str) -> (String, bool) {
    let char_count = output.chars().count();
    if char_count <= MAX_OUTPUT_CHARS {
        return (output.to_string(), false);
    }
    let half = MAX_OUTPUT_CHARS / 2;
    let head: String = output.chars().take(half).collect();
    let tail: String = output.chars().rev().take(half).collect::<String>().chars().rev().collect();
    let truncated_kb = (output.len() - MAX_OUTPUT_CHARS) as f64 / 1024.0;
    (
        format!("{head}\n\n[... {truncated_kb:.0}KB truncated ...]\n\n{tail}"),
        true,
    )
}

#[async_trait::async_trait]
impl super::Tool for BashTool {
    fn name(&self) -> &str {
        "bash"
    }

    fn description(&self) -> &str {
        "Execute a shell command. Default timeout 120s. Max output 30KB."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)"}
            },
            "required": ["command"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::Execute
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let command = args["command"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'command' parameter"))?;
        let timeout = args["timeout"]
            .as_u64()
            .unwrap_or(DEFAULT_TIMEOUT_SECS);

        // Check deny list
        if let Some(reason) = self.is_denied(command) {
            return Ok(ToolResult {
                content: reason,
                is_error: true,
                truncated: false,
            });
        }

        let result = tokio::time::timeout(
            Duration::from_secs(timeout),
            Command::new("sh")
                .arg("-c")
                .arg(command)
                .output(),
        )
        .await;

        match result {
            Ok(Ok(output)) => {
                let stdout = String::from_utf8_lossy(&output.stdout);
                let stderr = String::from_utf8_lossy(&output.stderr);
                let code = output.status.code().unwrap_or(-1);

                let combined = if stderr.is_empty() {
                    stdout.to_string()
                } else {
                    format!("{stdout}\n[stderr]\n{stderr}")
                };

                let (text, truncated) = truncate_output(&combined);
                let content = format!("[exit code: {code}]\n{text}");

                Ok(ToolResult {
                    content,
                    is_error: code != 0,
                    truncated,
                })
            }
            Ok(Err(e)) => Ok(ToolResult {
                content: format!("Failed to execute command: {e}"),
                is_error: true,
                truncated: false,
            }),
            Err(_) => Ok(ToolResult {
                content: format!("[TIMEOUT after {timeout}s] Command killed: {command}"),
                is_error: true,
                truncated: false,
            }),
        }
    }
}
