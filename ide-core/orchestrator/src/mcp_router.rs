use anyhow::Result;
use tracing::{info, warn};
use uuid::Uuid;

use crate::config::Config;
use crate::context_manager::truncate_context;
use crate::llm_client::LlmClient;
use crate::types::*;

/// Available tools the Router (Gemma 4) can invoke
fn orchestrator_tools() -> Vec<ToolDef> {
    vec![
        ToolDef {
            tool_type: "function".to_string(),
            function: FunctionDef {
                name: "get_financial_report".to_string(),
                description: "Get financial report for a Vietnamese stock ticker".to_string(),
                parameters: serde_json::json!({
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker (e.g. VNM)"},
                        "year": {"type": "integer"},
                        "quarter": {"type": "integer"}
                    },
                    "required": ["ticker"]
                }),
            },
        },
        ToolDef {
            tool_type: "function".to_string(),
            function: FunctionDef {
                name: "get_credit_score_data".to_string(),
                description: "Get SME credit scoring data for a ticker".to_string(),
                parameters: serde_json::json!({
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"}
                    },
                    "required": ["ticker"]
                }),
            },
        },
        // bash-executor removed until sandboxed Rust implementation is complete
    ]
}

/// Check if response content contains code blocks
fn has_code_blocks(response: &ChatResponse) -> bool {
    response
        .choices
        .first()
        .and_then(|c| c.message.content.as_deref())
        .map(|c| c.contains("```"))
        .unwrap_or(false)
}

/// Check if response has tool calls
fn has_tool_calls(response: &ChatResponse) -> bool {
    response
        .choices
        .first()
        .and_then(|c| c.message.tool_calls.as_ref())
        .map(|calls| !calls.is_empty())
        .unwrap_or(false)
}

/// Execute tool calls by dispatching to MCP tool servers (stub for now)
async fn execute_tool_calls(calls: &[ToolCall]) -> Vec<ChatMessage> {
    let mut results = Vec::new();
    for call in calls {
        // TODO: dispatch to actual MCP tool servers via HTTP
        let result = format!(
            "{{\"status\": \"ok\", \"tool\": \"{}\", \"note\": \"stub result — wire to MCP server\"}}",
            call.function.name
        );
        results.push(ChatMessage {
            role: "tool".to_string(),
            content: Some(result),
            tool_calls: None,
            tool_call_id: Some(call.id.clone()),
        });
    }
    results
}

/// The 4-step routing pipeline
pub async fn route_request(
    config: &Config,
    client: &LlmClient,
    request: ChatRequest,
) -> Result<ChatResponse> {
    let mut messages = request.messages;
    let mut total_usage = Usage::default();

    // Step 1: Architect (Gemma 4) — routing + planning
    info!("Step 1: Sending to Router (port {})", config.router_port);
    truncate_context(&mut messages, config.max_context_tokens);
    let tools = orchestrator_tools();
    let architect_resp = client
        .chat_completion(config.router_port, &messages, Some(&tools), 180)
        .await?;
    total_usage.merge(&architect_resp.usage);

    let architect_msg = architect_resp
        .choices
        .first()
        .map(|c| c.message.clone())
        .unwrap_or(ChatMessage {
            role: "assistant".to_string(),
            content: Some("No response from router".to_string()),
            tool_calls: None,
            tool_call_id: None,
        });
    messages.push(architect_msg.clone());

    // Step 2: Tool execution (if Gemma requested tools)
    if has_tool_calls(&architect_resp) {
        info!("Step 2: Executing tool calls");
        let calls = architect_msg.tool_calls.as_deref().unwrap_or_default();
        let tool_results = execute_tool_calls(calls).await;
        messages.extend(tool_results);
    } else {
        info!("Step 2: No tool calls — skipping");
    }

    // Step 3: Reasoning (DeepSeek R1) — if complex code/logic needed
    let needs_reasoning = has_code_blocks(&architect_resp) || has_tool_calls(&architect_resp);
    let mut last_response = architect_resp;

    if needs_reasoning {
        info!(
            "Step 3: Sending to Reasoning (port {})",
            config.reasoning_port
        );
        truncate_context(&mut messages, config.max_context_tokens);
        let reasoning_resp = client
            .chat_completion(config.reasoning_port, &messages, None, 300)
            .await?;
        total_usage.merge(&reasoning_resp.usage);

        if let Some(msg) = reasoning_resp.choices.first().map(|c| c.message.clone()) {
            messages.push(msg);
        }
        last_response = reasoning_resp;
    } else {
        info!("Step 3: Simple query — skipping reasoning");
    }

    // Step 4: Audit (Qwen Coder) — if code was generated
    if has_code_blocks(&last_response) {
        info!("Step 4: Sending to Audit (port {})", config.audit_port);
        let audit_prompt = ChatMessage {
            role: "system".to_string(),
            content: Some(
                "Review the code above for security vulnerabilities, bugs, and clean code violations. \
                 Return corrected code with brief explanations of changes."
                    .to_string(),
            ),
            tool_calls: None,
            tool_call_id: None,
        };
        messages.push(audit_prompt);
        truncate_context(&mut messages, config.max_context_tokens);

        match client
            .chat_completion(config.audit_port, &messages, None, 120)
            .await
        {
            Ok(audit_resp) => {
                total_usage.merge(&audit_resp.usage);
                last_response = audit_resp;
            }
            Err(e) => {
                warn!("Audit step failed (non-fatal): {e}");
            }
        }
    } else {
        info!("Step 4: No code to audit — skipping");
    }

    // Build final response
    let final_msg = last_response
        .choices
        .into_iter()
        .next()
        .map(|c| c.message)
        .unwrap_or(ChatMessage {
            role: "assistant".to_string(),
            content: Some("Pipeline completed with no output".to_string()),
            tool_calls: None,
            tool_call_id: None,
        });

    Ok(ChatResponse {
        id: format!("mekong-{}", Uuid::new_v4()),
        object: "chat.completion".to_string(),
        choices: vec![Choice {
            index: 0,
            message: final_msg,
            finish_reason: "stop".to_string(),
        }],
        usage: total_usage,
    })
}
