use axum::Json;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize)]
pub struct JsonRpcRequest {
    pub jsonrpc: String,
    pub id: Option<Value>,
    pub method: String,
    #[serde(default)]
    pub params: Value,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcResponse {
    pub jsonrpc: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<JsonRpcError>,
}

#[derive(Debug, Serialize)]
pub struct JsonRpcError {
    pub code: i32,
    pub message: String,
}

/// Handle MCP JSON-RPC 2.0 requests
pub async fn handle_mcp(Json(req): Json<JsonRpcRequest>) -> Json<JsonRpcResponse> {
    let result = match req.method.as_str() {
        "tools/list" => handle_tools_list(),
        "tools/call" => handle_tools_call(&req.params),
        _ => Err(JsonRpcError {
            code: -32601,
            message: format!("Method not found: {}", req.method),
        }),
    };

    Json(match result {
        Ok(value) => JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            id: req.id,
            result: Some(value),
            error: None,
        },
        Err(error) => JsonRpcResponse {
            jsonrpc: "2.0".to_string(),
            id: req.id,
            result: None,
            error: Some(error),
        },
    })
}

fn handle_tools_list() -> Result<Value, JsonRpcError> {
    Ok(serde_json::json!({
        "tools": [
            {
                "name": "code_assist",
                "description": "Multi-agent code assistance with routing, reasoning, and audit",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "The coding task or question"}
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "financial_analysis",
                "description": "Vietnamese stock market financial analysis via vnstock",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "analysis_type": {"type": "string", "enum": ["report", "credit_score", "price_history"]}
                    },
                    "required": ["ticker"]
                }
            },
            {
                "name": "file_operations",
                "description": "Safe file operations in sandboxed environment",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }
        ]
    }))
}

fn handle_tools_call(params: &Value) -> Result<Value, JsonRpcError> {
    let name = params
        .get("name")
        .and_then(|n| n.as_str())
        .unwrap_or("unknown");

    // Stub: return acknowledgment — real dispatch wired in integration phase
    Ok(serde_json::json!({
        "content": [{
            "type": "text",
            "text": format!("Tool '{}' invoked (stub). Wire to actual handler in integration phase.", name)
        }]
    }))
}
