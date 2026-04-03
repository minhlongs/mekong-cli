use anyhow::Result;
use serde_json::Value;

use super::{PermissionLevel, ToolResult};

pub struct AskUserTool;

#[async_trait::async_trait]
impl super::Tool for AskUserTool {
    fn name(&self) -> &str {
        "ask_user"
    }

    fn description(&self) -> &str {
        "Ask the user a question and wait for their response. Use when you need clarification."
    }

    fn parameters(&self) -> Value {
        serde_json::json!({
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask the user"}
            },
            "required": ["question"]
        })
    }

    fn permission_level(&self) -> PermissionLevel {
        PermissionLevel::ReadOnly
    }

    async fn execute(&self, args: Value) -> Result<ToolResult> {
        let question = args["question"]
            .as_str()
            .unwrap_or("Could you provide more details?");

        // Return a special marker that the orchestrator intercepts
        Ok(ToolResult {
            content: format!("[ASK_USER]{question}"),
            is_error: false,
            truncated: false,
        })
    }
}
