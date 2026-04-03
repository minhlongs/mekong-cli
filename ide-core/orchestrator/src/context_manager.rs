use anyhow::Context;
use tracing::{info, warn};

use crate::config::Config;
use crate::llm_client::LlmClient;
use crate::types::ChatMessage;

/// Trigger auto-compact at 75% capacity
const CONTEXT_WARNING_RATIO: f32 = 0.75;
/// Trigger full compact at 90% capacity
const CONTEXT_CRITICAL_RATIO: f32 = 0.90;
/// Max tokens for summary
const COMPACT_SUMMARY_BUDGET: usize = 4000;

/// Approximate token count: ~4 chars per token
pub fn estimate_tokens(text: &str) -> usize {
    text.len() / 4
}

/// Estimate total tokens across all messages
pub fn estimate_context_tokens(messages: &[ChatMessage]) -> usize {
    messages
        .iter()
        .map(|m| {
            let content_len = m.content.as_deref().unwrap_or("").len();
            let tool_len = m
                .tool_calls
                .as_ref()
                .map(|calls| {
                    calls
                        .iter()
                        .map(|c| c.function.name.len() + c.function.arguments.len())
                        .sum::<usize>()
                })
                .unwrap_or(0);
            (content_len + tool_len) / 4
        })
        .sum()
}

/// 3-layer context compression inspired by Claude Code
///
/// Layer 1: Quick trim — drop old tool results (cheapest, no LLM call)
/// Layer 2: Auto-compact — summarize via DeepSeek R1 when approaching limit
/// Layer 3: Emergency truncation — preserve only system + recent (last resort)
pub async fn compact_if_needed(
    messages: &mut Vec<ChatMessage>,
    max_tokens: usize,
    client: &LlmClient,
    config: &Config,
) {
    let current = estimate_context_tokens(messages);
    let ratio = current as f32 / max_tokens as f32;

    if ratio < CONTEXT_WARNING_RATIO {
        return; // Plenty of room
    }

    if ratio < CONTEXT_CRITICAL_RATIO {
        // Layer 1: Drop old tool results (keep last 5)
        quick_trim(messages);
        let after = estimate_context_tokens(messages);
        if (after as f32 / max_tokens as f32) < CONTEXT_WARNING_RATIO {
            info!("Quick trim sufficient: {} -> {} tokens", current, after);
            return;
        }
    }

    // Layer 2: Auto-compact via DeepSeek R1
    info!(
        "Auto-compact triggered at {:.0}% capacity",
        ratio * 100.0
    );
    if let Err(e) = auto_compact(messages, client, config).await {
        warn!("Auto-compact failed: {e}");
        // Layer 3: Emergency truncation (last resort)
        truncate_context(messages, max_tokens);
    }
}

/// Layer 1: Remove old tool result messages, keeping the last 5.
/// Also removes orphaned preceding assistant messages that only contain tool_calls
/// (no text content), since those become invalid once the tool result is gone.
fn quick_trim(messages: &mut Vec<ChatMessage>) {
    let tool_indices: Vec<usize> = messages
        .iter()
        .enumerate()
        .filter(|(_, m)| m.role == "tool")
        .map(|(i, _)| i)
        .collect();

    if tool_indices.len() <= 5 {
        return;
    }

    // Indices of tool messages to remove (oldest first)
    let to_remove: Vec<usize> = tool_indices[..tool_indices.len() - 5].to_vec();

    // Collect additional orphaned assistant indices (preceding tool-call-only messages)
    let mut extra_remove: Vec<usize> = Vec::new();
    for &tool_idx in &to_remove {
        if tool_idx > 0 {
            let prev = &messages[tool_idx - 1];
            // An assistant message is orphaned if it has tool_calls but no substantive content
            if prev.role == "assistant"
                && prev.tool_calls.as_ref().map_or(false, |tc| !tc.is_empty())
                && prev.content.as_deref().unwrap_or("").trim().is_empty()
            {
                extra_remove.push(tool_idx - 1);
            }
        }
    }

    // Combine, deduplicate, sort descending, and remove
    let mut all_remove = to_remove;
    all_remove.extend(extra_remove);
    all_remove.sort_unstable();
    all_remove.dedup();

    for idx in all_remove.into_iter().rev() {
        messages.remove(idx);
    }
}

/// Layer 2: Summarize conversation via LLM and replace old messages
async fn auto_compact(
    messages: &mut Vec<ChatMessage>,
    client: &LlmClient,
    config: &Config,
) -> anyhow::Result<()> {
    let conversation_text: String = messages
        .iter()
        .filter(|m| m.role != "system")
        .filter_map(|m| {
            let role = &m.role;
            let content = m.content.as_deref().unwrap_or("[tool call]");
            // Use char-based truncation to avoid splitting UTF-8 sequences
            let truncated: String = content.chars().take(500).collect();
            Some(format!("[{role}]: {truncated}"))
        })
        .collect::<Vec<_>>()
        .join("\n");

    let summary_prompt = vec![ChatMessage {
        role: "user".to_string(),
        content: Some(format!(
            "Summarize this conversation in under {COMPACT_SUMMARY_BUDGET} tokens. \
             Preserve: key decisions, file paths modified, current task state, \
             any errors encountered. Format as structured notes.\n\n{conversation_text}"
        )),
        tool_calls: None,
        tool_call_id: None,
    }];

    let summary_resp = client
        .chat_completion(config.reasoning_port, &summary_prompt, None, 60)
        .await
        .context("Summary generation failed")?;

    let summary = summary_resp
        .choices
        .first()
        .and_then(|c| c.message.content.as_deref())
        .unwrap_or("Failed to generate summary");

    // Replace conversation with: system messages + summary + last 3 messages
    let system_msgs: Vec<ChatMessage> = messages
        .iter()
        .filter(|m| m.role == "system")
        .cloned()
        .collect();
    let recent: Vec<ChatMessage> = messages
        .iter()
        .rev()
        .take(3)
        .cloned()
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect();

    messages.clear();
    messages.extend(system_msgs);
    messages.push(ChatMessage {
        role: "assistant".to_string(),
        content: Some(format!("[Context compacted]\n\n{summary}")),
        tool_calls: None,
        tool_call_id: None,
    });
    messages.extend(recent);

    info!("Auto-compact complete: {} messages remaining", messages.len());
    Ok(())
}

/// Layer 3: Emergency truncation — preserve system messages, first user message, last 2
pub fn truncate_context(messages: &mut Vec<ChatMessage>, max_tokens: usize) {
    let mut first_user_idx: Option<usize> = None;
    for (i, m) in messages.iter().enumerate() {
        if m.role == "user" {
            first_user_idx = Some(i);
            break;
        }
    }

    while estimate_context_tokens(messages) > max_tokens && messages.len() > 2 {
        let removable = messages.iter().enumerate().position(|(i, m)| {
            m.role != "system"
                && Some(i) != first_user_idx
                && i < messages.len().saturating_sub(2)
        });
        match removable {
            Some(idx) => {
                warn!("Context overflow: dropping message at index {idx}");
                messages.remove(idx);
                if let Some(ref mut fui) = first_user_idx {
                    if idx < *fui {
                        *fui -= 1;
                    }
                }
            }
            None => break,
        }
    }
}
