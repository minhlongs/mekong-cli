/// LLM health-check and chat-completion commands.
/// Probes MLX at :11435, Ollama at :11434, and the local gateway at :8000.
use serde::{Deserialize, Serialize};

// ── Response types ────────────────────────────────────────────────────────────

#[derive(Serialize)]
pub struct EngineStatus {
    pub online: bool,
    pub models: Vec<String>,
    pub port: u16,
}

#[derive(Serialize)]
pub struct LlmHealthResponse {
    pub mlx: EngineStatus,
    pub ollama: EngineStatus,
}

#[derive(Serialize)]
pub struct GatewayHealth {
    pub online: bool,
    pub version: Option<String>,
    pub timestamp: Option<String>,
}

#[derive(Deserialize)]
struct OllamaTagsResponse {
    models: Option<Vec<OllamaModel>>,
}

#[derive(Deserialize)]
struct OllamaModel {
    name: String,
}

#[derive(Deserialize)]
struct OpenAiModelsResponse {
    data: Option<Vec<OpenAiModel>>,
}

#[derive(Deserialize)]
struct OpenAiModel {
    id: String,
}

#[derive(Deserialize)]
struct GatewayHealthBody {
    version: Option<String>,
    timestamp: Option<String>,
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async fn http_get_json<T: for<'de> Deserialize<'de>>(url: &str) -> Option<T> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(3))
        .build()
        .ok()?;
    let resp = client.get(url).send().await.ok()?;
    if resp.status().is_success() {
        resp.json::<T>().await.ok()
    } else {
        None
    }
}

async fn probe_ollama() -> EngineStatus {
    const PORT: u16 = 11434;
    match http_get_json::<OllamaTagsResponse>(&format!("http://localhost:{PORT}/api/tags")).await {
        Some(body) => {
            let models = body
                .models
                .unwrap_or_default()
                .into_iter()
                .map(|m| m.name)
                .collect();
            EngineStatus { online: true, models, port: PORT }
        }
        None => EngineStatus { online: false, models: vec![], port: PORT },
    }
}

async fn probe_mlx() -> EngineStatus {
    const PORT: u16 = 11435;
    match http_get_json::<OpenAiModelsResponse>(&format!("http://localhost:{PORT}/v1/models")).await
    {
        Some(body) => {
            let models = body
                .data
                .unwrap_or_default()
                .into_iter()
                .map(|m| m.id)
                .collect();
            EngineStatus { online: true, models, port: PORT }
        }
        None => EngineStatus { online: false, models: vec![], port: PORT },
    }
}

// ── Commands ──────────────────────────────────────────────────────────────────

/// Probe MLX (:11435) and Ollama (:11434) concurrently.
#[tauri::command]
pub async fn check_llm_health() -> Result<LlmHealthResponse, String> {
    let (mlx, ollama) = tokio::join!(probe_mlx(), probe_ollama());
    Ok(LlmHealthResponse { mlx, ollama })
}

/// GET localhost:8000/health
#[tauri::command]
pub async fn check_gateway_health() -> Result<GatewayHealth, String> {
    match http_get_json::<GatewayHealthBody>("http://localhost:8000/health").await {
        Some(body) => Ok(GatewayHealth {
            online: true,
            version: body.version,
            timestamp: body.timestamp,
        }),
        None => Ok(GatewayHealth { online: false, version: None, timestamp: None }),
    }
}

/// POST to MLX (:11435) or fall back to Ollama (:11434) for chat completion.
/// Returns the assistant message content string.
#[tauri::command]
pub async fn chat_completion(model: String, message: String) -> Result<String, String> {
    #[derive(Serialize)]
    struct ChatMessage {
        role: String,
        content: String,
    }
    #[derive(Serialize)]
    struct ChatRequest {
        model: String,
        messages: Vec<ChatMessage>,
        max_tokens: u32,
    }
    #[derive(Deserialize)]
    struct ChatResponse {
        choices: Option<Vec<Choice>>,
    }
    #[derive(Deserialize)]
    struct Choice {
        message: Option<AssistantMessage>,
    }
    #[derive(Deserialize)]
    struct AssistantMessage {
        content: Option<String>,
    }

    let payload = ChatRequest {
        model: model.clone(),
        messages: vec![ChatMessage { role: "user".to_string(), content: message }],
        max_tokens: 2048,
    };

    // Try MLX first; fall back to Ollama
    let endpoints = ["http://localhost:11435/v1/chat/completions",
                     "http://localhost:11434/v1/chat/completions"];

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;

    for url in endpoints {
        let resp = client
            .post(url)
            .json(&payload)
            .send()
            .await;

        if let Ok(r) = resp {
            if r.status().is_success() {
                let body: ChatResponse = r.json().await.map_err(|e| e.to_string())?;
                let content = body
                    .choices
                    .unwrap_or_default()
                    .into_iter()
                    .next()
                    .and_then(|c| c.message)
                    .and_then(|m| m.content)
                    .unwrap_or_default();
                return Ok(content);
            }
        }
    }

    Err(format!("No LLM endpoint available for model '{model}'"))
}
