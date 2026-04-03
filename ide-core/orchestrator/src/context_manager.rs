use crate::types::ChatMessage;

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
            estimate_tokens(&format!(
                "{}{}",
                "x".repeat(content_len),
                "x".repeat(tool_len)
            ))
        })
        .sum()
}

/// Trim middle messages to fit within max_tokens.
/// Preserves: system messages, first user message, and last 2 messages.
pub fn truncate_context(messages: &mut Vec<ChatMessage>, max_tokens: usize) {
    let mut first_user_idx: Option<usize> = None;
    for (i, m) in messages.iter().enumerate() {
        if m.role == "user" {
            first_user_idx = Some(i);
            break;
        }
    }

    while estimate_context_tokens(messages) > max_tokens && messages.len() > 2 {
        // Find a removable message: not system, not first user, not last 2
        let removable = messages.iter().enumerate().position(|(i, m)| {
            m.role != "system"
                && Some(i) != first_user_idx
                && i < messages.len().saturating_sub(2)
        });
        match removable {
            Some(idx) => {
                tracing::warn!("Context overflow: dropping message at index {idx}");
                messages.remove(idx);
                // Adjust first_user_idx if needed
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
