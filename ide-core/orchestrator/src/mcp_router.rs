use anyhow::Result;
use tracing::{info, warn};
use uuid::Uuid;

use crate::config::Config;
use crate::context_manager::compact_if_needed;
use crate::llm_client::LlmClient;
use crate::permissions::{PermissionCheck, PermissionGuard};
use crate::tools::{ToolRegistry, ToolResult};
use crate::types::*;

/// Dynamic agent loop — model drives, harness executes.
///
/// Replaces the old 4-step rigid pipeline (Architect -> Tools -> Reasoning -> Audit)
/// with a loop where the Architect (Gemma 4) stays in control, calling tools
/// and sub-models until it emits a final answer with no tool calls.
pub async fn route_request(
    config: &Config,
    client: &LlmClient,
    tools: &ToolRegistry,
    permissions: &PermissionGuard,
    request: ChatRequest,
) -> Result<ChatResponse> {
    let mut messages = request.messages;
    let mut total_usage = Usage::default();
    let max_iterations = 25;

    // Load MEKONG.md project context if exists
    if let Some(project_ctx) = tools.read_project_file() {
        messages.insert(
            0,
            ChatMessage {
                role: "system".to_string(),
                content: Some(project_ctx),
                tool_calls: None,
                tool_call_id: None,
            },
        );
    }

    // Build tool definitions (real tools + meta-tools for reasoning/audit)
    let mut tool_defs = tools.all_tool_defs();

    // Add DeepSeek R1 as a callable "tool"
    tool_defs.push(ToolDef {
        tool_type: "function".to_string(),
        function: FunctionDef {
            name: "deep_reasoning".to_string(),
            description: "Invoke DeepSeek R1 32B for complex reasoning, math, or code generation. \
                          Use for tasks requiring chain-of-thought analysis."
                .to_string(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The problem or code task to reason about"}
                },
                "required": ["prompt"]
            }),
        },
    });

    // Add Qwen Audit as a callable "tool"
    tool_defs.push(ToolDef {
        tool_type: "function".to_string(),
        function: FunctionDef {
            name: "code_audit".to_string(),
            description: "Invoke Qwen2.5-Coder 7B to review code for security vulnerabilities, \
                          bugs, and style issues."
                .to_string(),
            parameters: serde_json::json!({
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The code to review"}
                },
                "required": ["code"]
            }),
        },
    });

    for iteration in 0..max_iterations {
        info!("Agent loop iteration {}/{}", iteration + 1, max_iterations);

        // Context management before each LLM call
        compact_if_needed(&mut messages, config.max_context_tokens, client, config).await;

        // Call Architect (Gemma 4)
        let response = client
            .chat_completion(config.router_port, &messages, Some(&tool_defs), 180)
            .await?;
        total_usage.merge(&response.usage);

        let choice = response
            .choices
            .first()
            .ok_or_else(|| anyhow::anyhow!("Empty response from Architect"))?;
        let msg = choice.message.clone();
        messages.push(msg.clone());

        // Check for tool calls
        let tool_calls = msg.tool_calls.as_deref().unwrap_or_default();
        if tool_calls.is_empty() {
            // No tool calls = final answer
            info!("Agent loop complete after {} iterations", iteration + 1);
            return Ok(ChatResponse {
                id: format!("mekong-{}", Uuid::new_v4()),
                object: "chat.completion".to_string(),
                choices: vec![Choice {
                    index: 0,
                    message: msg,
                    finish_reason: "stop".to_string(),
                }],
                usage: total_usage,
            });
        }

        // Execute each tool call
        for call in tool_calls {
            let result = match call.function.name.as_str() {
                "deep_reasoning" => {
                    execute_reasoning(client, config, &call.function.arguments, &mut total_usage)
                        .await
                }
                "code_audit" => {
                    execute_audit(client, config, &call.function.arguments, &mut total_usage).await
                }
                tool_name => {
                    execute_tool(tools, permissions, tool_name, &call.function.arguments).await
                }
            };

            // Feed tool result back into conversation
            messages.push(ChatMessage {
                role: "tool".to_string(),
                content: Some(result.content),
                tool_calls: None,
                tool_call_id: Some(call.id.clone()),
            });
        }
    }

    // Safety cap reached
    warn!("Agent loop hit max iterations ({max_iterations})");
    Ok(ChatResponse {
        id: format!("mekong-{}", Uuid::new_v4()),
        object: "chat.completion".to_string(),
        choices: vec![Choice {
            index: 0,
            message: ChatMessage {
                role: "assistant".to_string(),
                content: Some("Max iterations reached. Partial results above.".to_string()),
                tool_calls: None,
                tool_call_id: None,
            },
            finish_reason: "length".to_string(),
        }],
        usage: total_usage,
    })
}

/// Route to DeepSeek R1 for complex reasoning
async fn execute_reasoning(
    client: &LlmClient,
    config: &Config,
    arguments: &str,
    total_usage: &mut Usage,
) -> ToolResult {
    let args: serde_json::Value = match serde_json::from_str(arguments) {
        Ok(v) => v,
        Err(e) => {
            return ToolResult {
                content: format!("Invalid arguments: {e}"),
                is_error: true,
                truncated: false,
            }
        }
    };
    let prompt = args["prompt"].as_str().unwrap_or("");
    let reasoning_msgs = vec![ChatMessage {
        role: "user".to_string(),
        content: Some(prompt.to_string()),
        tool_calls: None,
        tool_call_id: None,
    }];
    match client
        .chat_completion(config.reasoning_port, &reasoning_msgs, None, 300)
        .await
    {
        Ok(resp) => {
            total_usage.merge(&resp.usage);
            let content = resp
                .choices
                .first()
                .and_then(|c| c.message.content.as_deref())
                .unwrap_or("No reasoning output");
            ToolResult {
                content: content.to_string(),
                is_error: false,
                truncated: false,
            }
        }
        Err(e) => ToolResult {
            content: format!("Reasoning error: {e}"),
            is_error: true,
            truncated: false,
        },
    }
}

/// Route to Qwen Coder for security/style audit
async fn execute_audit(
    client: &LlmClient,
    config: &Config,
    arguments: &str,
    total_usage: &mut Usage,
) -> ToolResult {
    let args: serde_json::Value = match serde_json::from_str(arguments) {
        Ok(v) => v,
        Err(e) => {
            return ToolResult {
                content: format!("Invalid arguments: {e}"),
                is_error: true,
                truncated: false,
            }
        }
    };
    let code = args["code"].as_str().unwrap_or("");
    let audit_msgs = vec![ChatMessage {
        role: "user".to_string(),
        content: Some(format!(
            "Review this code for security, bugs, and style:\n\n{code}"
        )),
        tool_calls: None,
        tool_call_id: None,
    }];
    match client
        .chat_completion(config.audit_port, &audit_msgs, None, 120)
        .await
    {
        Ok(resp) => {
            total_usage.merge(&resp.usage);
            let content = resp
                .choices
                .first()
                .and_then(|c| c.message.content.as_deref())
                .unwrap_or("No audit output");
            ToolResult {
                content: content.to_string(),
                is_error: false,
                truncated: false,
            }
        }
        Err(e) => ToolResult {
            content: format!("Audit error: {e}"),
            is_error: true,
            truncated: false,
        },
    }
}

/// Execute a tool via the registry with permission checks
async fn execute_tool(
    tools: &ToolRegistry,
    permissions: &PermissionGuard,
    tool_name: &str,
    arguments: &str,
) -> ToolResult {
    // Permission check
    if let Some(level) = tools.permission_level(tool_name) {
        match permissions.check(tool_name, &level, arguments) {
            PermissionCheck::Allowed => {}
            PermissionCheck::Denied(reason) => {
                return ToolResult {
                    content: format!("Permission denied: {reason}"),
                    is_error: true,
                    truncated: false,
                };
            }
            PermissionCheck::NeedsApproval(reason) => {
                // Non-interactive server mode: deny operations that require human approval
                warn!("Denied in non-interactive mode: {reason}");
                return ToolResult {
                    content: format!("Permission denied (non-interactive): {reason}"),
                    is_error: true,
                    truncated: false,
                };
            }
        }
    }

    let args: serde_json::Value =
        serde_json::from_str(arguments).unwrap_or(serde_json::json!({}));
    tools.execute(tool_name, args).await.unwrap_or_else(|e| {
        ToolResult {
            content: format!("Tool error: {e}"),
            is_error: true,
            truncated: false,
        }
    })
}
