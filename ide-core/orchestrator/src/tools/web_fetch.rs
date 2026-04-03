use anyhow::Result;
use serde_json::Value;
use std::time::Duration;

use super::{PermissionLevel, ToolResult};

const MAX_CHARS: usize = 50_000;
const TIMEOUT_SECS: u64 = 30;

pub struct WebFetchTool;

/// Strip HTML tags naively for plain text extraction
fn strip_html(html: &str) -> String {
    let mut result = String::with_capacity(html.len());
    let mut in_tag = false;
    let mut in_script = false;
    for c in html.chars() {
        match c {
            '<' => {
                in_tag = true;
                // Check for script/style start
                let rest: String = html[html.len().saturating_sub(html.len())..].chars().take(20).collect();
                if rest.to_lowercase().starts_with("<script") || rest.to_lowercase().starts_with("<style") {
                    in_script = true;
                }
            }
            '>' => {
                in_tag = false;
                if in_script {
                    in_script = false;
                }
            }
            _ if !in_tag && !in_script => result.push(c),
            _ => {}
        }
    }
    // Collapse whitespace
    let mut prev_space = false;
    result
        .chars()
        .filter(|c| {
            if c.is_whitespace() {
                if prev_space {
                    return false;
                }
                prev_space = true;
            } else {
                prev_space = false;
            }
            true
        })
        .collect()
}

#[async_trait::async_trait]
impl super::Tool for WebFetchTool {
    fn name(&self) -> &str {
        "web_fetch"
    }

    fn description(&self) -> &str {
        "Fetch URL content. Strips HTML to plain text. Max 50KB. 30s timeout."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"}
            },
            "required": ["url"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let url = args["url"]
            .as_str()
            .ok_or_else(|| anyhow::anyhow!("Missing 'url' parameter"))?;

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(TIMEOUT_SECS))
            .build()?;

        let response = match client.get(url).send().await {
            Ok(r) => r,
            Err(e) => {
                return Ok(ToolResult {
                    content: format!("Fetch error: {e}"),
                    is_error: true,
                    truncated: false,
                });
            }
        };

        let status = response.status();
        let body = response.text().await.unwrap_or_default();

        let text = strip_html(&body);
        let truncated = text.len() > MAX_CHARS;
        let content = if truncated {
            format!(
                "[HTTP {status}]\n{}\n\n[... truncated at {MAX_CHARS} chars ...]",
                &text[..MAX_CHARS]
            )
        } else {
            format!("[HTTP {status}]\n{text}")
        };

        Ok(ToolResult {
            content,
            is_error: !status.is_success(),
            truncated,
        })
    }
}
