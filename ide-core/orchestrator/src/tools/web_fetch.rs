use anyhow::Result;
use regex::Regex;
use serde_json::Value;
use std::time::Duration;

use super::{PermissionLevel, ToolResult};

const MAX_CHARS: usize = 50_000;
const TIMEOUT_SECS: u64 = 30;
const MAX_REDIRECTS: usize = 3;

pub struct WebFetchTool;

/// Returns true if the URL targets a private/internal network address (SSRF guard).
fn is_private_url(url: &str) -> bool {
    let url_lower = url.to_lowercase();

    // Block file:// scheme
    if url_lower.starts_with("file://") {
        return true;
    }

    // Block known private/loopback hostnames and prefixes
    let blocked_prefixes = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "[::1]",
        "169.254.",
        "metadata.google.",
        "169.254.169.254",
    ];
    for prefix in &blocked_prefixes {
        if url_lower.contains(prefix) {
            return true;
        }
    }

    // Block 10.x.x.x
    let re_10 = Regex::new(r"[:/\.]10\.(\d{1,3})\.").unwrap();
    if re_10.is_match(&url_lower) {
        return true;
    }

    // Block 172.16-31.x.x
    let re_172 = Regex::new(r"172\.(1[6-9]|2\d|3[01])\.").unwrap();
    if re_172.is_match(&url_lower) {
        return true;
    }

    // Block 192.168.x.x
    let re_192 = Regex::new(r"192\.168\.").unwrap();
    if re_192.is_match(&url_lower) {
        return true;
    }

    false
}

/// Strip HTML tags using a character-level state machine.
/// Properly skips script and style block content (no XSS leakage).
fn strip_html(html: &str) -> String {
    let mut result = String::with_capacity(html.len() / 2);
    let mut chars = html.chars().peekable();
    let mut in_tag = false;
    let mut in_script_style = false;
    let mut tag_buf = String::new();

    while let Some(c) = chars.next() {
        if in_script_style {
            // Inside a script/style block — scan for the closing tag
            if c == '<' {
                // Accumulate up to 9 more chars to detect </script> or </style>
                tag_buf.clear();
                tag_buf.push(c);
                for _ in 0..8 {
                    if let Some(&nc) = chars.peek() {
                        tag_buf.push(nc);
                        chars.next();
                        if nc == '>' {
                            break;
                        }
                    }
                }
                let tag_lower = tag_buf.to_lowercase();
                if tag_lower.starts_with("</script") || tag_lower.starts_with("</style") {
                    // Closing tag found — exit script/style mode
                    in_script_style = false;
                    in_tag = false;
                }
                // Always skip tag_buf content (don't emit script/style text)
            }
            // All other chars inside script/style are silently dropped
            continue;
        }

        match c {
            '<' => {
                in_tag = true;
                tag_buf.clear();
                tag_buf.push(c);
            }
            '>' => {
                tag_buf.push(c);
                let tag_lower = tag_buf.to_lowercase();
                // Detect opening <script or <style (not self-closing variants)
                if (tag_lower.starts_with("<script") || tag_lower.starts_with("<style"))
                    && !tag_lower.ends_with("/>")
                {
                    in_script_style = true;
                }
                in_tag = false;
                tag_buf.clear();
            }
            _ => {
                if in_tag {
                    tag_buf.push(c);
                } else {
                    result.push(c);
                }
            }
        }
    }

    // Collapse consecutive whitespace into a single space
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
        "Fetch URL content. Strips HTML to plain text. Max 50KB. 30s timeout. Private/internal URLs are blocked."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch (must be a public internet URL)"}
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

        // SSRF protection: block private/internal addresses
        if is_private_url(url) {
            return Ok(ToolResult {
                content: format!("Blocked: URL targets a private or internal address: {url}"),
                is_error: true,
                truncated: false,
            });
        }

        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(TIMEOUT_SECS))
            .redirect(reqwest::redirect::Policy::limited(MAX_REDIRECTS))
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
        let display: String = text.chars().take(MAX_CHARS).collect();
        let content = if truncated {
            format!(
                "[HTTP {status}]\n{display}\n\n[... truncated at {MAX_CHARS} chars ...]"
            )
        } else {
            format!("[HTTP {status}]\n{display}")
        };

        Ok(ToolResult {
            content,
            is_error: !status.is_success(),
            truncated,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ssrf_blocks_localhost() {
        assert!(is_private_url("http://localhost/admin"));
        assert!(is_private_url("http://127.0.0.1:8080/"));
        assert!(is_private_url("http://0.0.0.0/"));
        assert!(is_private_url("http://[::1]/"));
    }

    #[test]
    fn test_ssrf_blocks_metadata() {
        assert!(is_private_url("http://169.254.169.254/latest/meta-data/"));
        assert!(is_private_url("http://metadata.google.internal/"));
    }

    #[test]
    fn test_ssrf_blocks_private_ranges() {
        assert!(is_private_url("http://192.168.1.1/"));
        assert!(is_private_url("http://172.16.0.1/"));
        assert!(is_private_url("http://172.31.255.255/"));
        assert!(!is_private_url("http://172.15.0.1/"));
        assert!(!is_private_url("http://172.32.0.1/"));
    }

    #[test]
    fn test_ssrf_blocks_file_scheme() {
        assert!(is_private_url("file:///etc/passwd"));
    }

    #[test]
    fn test_ssrf_allows_public() {
        assert!(!is_private_url("https://example.com/"));
        assert!(!is_private_url("https://api.github.com/repos"));
    }

    #[test]
    fn test_strip_html_removes_script() {
        let html = "<html><head><script>alert('xss')</script></head><body>Hello</body></html>";
        let result = strip_html(html);
        assert!(!result.contains("alert"));
        assert!(result.contains("Hello"));
    }
}
