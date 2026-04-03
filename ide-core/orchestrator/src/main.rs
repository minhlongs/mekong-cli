mod config;
mod context_manager;
mod llm_client;
mod mcp_handler;
mod mcp_router;
mod permissions;
mod project;
mod tools;
mod types;

use std::sync::Arc;

use axum::{
    extract::{DefaultBodyLimit, State},
    routing::{get, post},
    Json, Router,
};
use tower_http::cors::{AllowOrigin, CorsLayer};
use tracing::info;

use crate::config::Config;
use crate::llm_client::LlmClient;
use crate::mcp_handler::handle_mcp;
use crate::permissions::PermissionGuard;
use crate::tools::ToolRegistry;
use crate::types::{ChatRequest, ChatResponse};

#[derive(Clone)]
pub struct AppState {
    pub config: Config,
    pub llm_client: LlmClient,
    pub tool_registry: Arc<ToolRegistry>,
    pub permission_guard: Arc<PermissionGuard>,
}

async fn chat_completions(
    State(state): State<Arc<AppState>>,
    Json(request): Json<ChatRequest>,
) -> Result<Json<ChatResponse>, (axum::http::StatusCode, String)> {
    mcp_router::route_request(
        &state.config,
        &state.llm_client,
        &state.tool_registry,
        &state.permission_guard,
        request,
    )
    .await
    .map(Json)
    .map_err(|e| {
        tracing::error!("Pipeline error: {e:#}");
        (
            axum::http::StatusCode::BAD_GATEWAY,
            "Internal pipeline error. Check server logs.".to_string(),
        )
    })
}

async fn list_models() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "object": "list",
        "data": [
            {"id": "mekong-orchestrator", "object": "model", "owned_by": "mekong-ide"},
            {"id": "gemma-4-26b-a4b", "object": "model", "owned_by": "google"},
            {"id": "deepseek-r1-32b", "object": "model", "owned_by": "deepseek"},
            {"id": "qwen2.5-coder-7b", "object": "model", "owned_by": "alibaba"}
        ]
    }))
}

async fn health(State(state): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let cfg = &state.config;
    let client = &state.llm_client;

    let router_ok = client.is_healthy(cfg.router_port).await;
    let reasoning_ok = client.is_healthy(cfg.reasoning_port).await;
    let audit_ok = client.is_healthy(cfg.audit_port).await;

    let tool_count = state.tool_registry.all_tool_defs().len();

    Json(serde_json::json!({
        "status": if router_ok && reasoning_ok && audit_ok { "healthy" } else { "degraded" },
        "engines": {
            "router": { "port": cfg.router_port, "healthy": router_ok },
            "reasoning": { "port": cfg.reasoning_port, "healthy": reasoning_ok },
            "audit": { "port": cfg.audit_port, "healthy": audit_ok }
        },
        "tools": tool_count,
        "mode": "dynamic_agent_loop"
    }))
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "mekong_orchestrator=info".into()),
        )
        .init();

    let config = Config::from_env();
    let port = config.orchestrator_port;

    // Initialize tool registry with current directory as workspace
    let workspace = std::env::current_dir()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|_| ".".to_string());
    let tool_registry = Arc::new(ToolRegistry::new(&workspace));
    let permission_guard = Arc::new(PermissionGuard::from_env());

    info!(
        "Tool registry: {} tools loaded",
        tool_registry.all_tool_defs().len()
    );
    info!(
        "Permission mode: {:?}",
        std::env::var("MEKONG_PERMISSION_MODE").unwrap_or_else(|_| "allow_edits".to_string())
    );

    let state = Arc::new(AppState {
        llm_client: LlmClient::new(&config.llm_host),
        config,
        tool_registry,
        permission_guard,
    });

    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::predicate(|origin, _| {
            let host = origin.as_bytes();
            host.starts_with(b"http://127.0.0.1")
                || host.starts_with(b"http://localhost")
                || host.starts_with(b"vscode-webview://")
        }))
        .allow_methods(tower_http::cors::Any)
        .allow_headers(tower_http::cors::Any);

    let app = Router::new()
        .route("/v1/chat/completions", post(chat_completions))
        .route("/v1/models", get(list_models))
        .route("/health", get(health))
        .route("/mcp", post(handle_mcp))
        .layer(DefaultBodyLimit::max(1_048_576))
        .layer(cors)
        .with_state(state);

    let addr = format!("0.0.0.0:{port}");
    info!("Mekong Orchestrator starting on {addr}");
    info!("Endpoints: POST /v1/chat/completions, GET /v1/models, GET /health, POST /mcp");
    info!("Mode: Dynamic Agent Loop (max 25 iterations)");

    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("failed to bind");

    axum::serve(listener, app).await.expect("server crashed");
}
