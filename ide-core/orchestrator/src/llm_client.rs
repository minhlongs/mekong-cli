use anyhow::{Context, Result};
use reqwest::Client;
use std::time::Duration;

use crate::types::{ChatMessage, ChatResponse, ToolDef};

#[derive(Clone)]
pub struct LlmClient {
    client: Client,
    host: String,
}

impl LlmClient {
    pub fn new(host: &str) -> Self {
        let client = Client::builder()
            .timeout(Duration::from_secs(180))
            .build()
            .expect("failed to build HTTP client");
        Self {
            client,
            host: host.to_string(),
        }
    }

    pub async fn chat_completion(
        &self,
        port: u16,
        messages: &[ChatMessage],
        tools: Option<&[ToolDef]>,
        timeout_secs: u64,
    ) -> Result<ChatResponse> {
        let url = format!("http://{}:{}/v1/chat/completions", self.host, port);

        let mut body = serde_json::json!({
            "messages": messages,
            "max_tokens": 2048,
        });

        if let Some(tools) = tools {
            body["tools"] = serde_json::to_value(tools)?;
        }

        let response = self
            .client
            .post(&url)
            .timeout(Duration::from_secs(timeout_secs))
            .json(&body)
            .send()
            .await
            .with_context(|| format!("failed to reach LLM at {url}"))?;

        let status = response.status();
        if !status.is_success() {
            let text = response.text().await.unwrap_or_default();
            anyhow::bail!("LLM returned {status}: {text}");
        }

        response
            .json::<ChatResponse>()
            .await
            .context("failed to parse LLM response")
    }

    /// Quick health check — returns true if /v1/models responds 200
    pub async fn is_healthy(&self, port: u16) -> bool {
        let url = format!("http://{}:{}/v1/models", self.host, port);
        self.client
            .get(&url)
            .timeout(Duration::from_secs(5))
            .send()
            .await
            .map(|r| r.status().is_success())
            .unwrap_or(false)
    }
}
