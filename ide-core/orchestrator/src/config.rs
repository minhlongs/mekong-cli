use std::env;

#[derive(Debug, Clone)]
pub struct Config {
    pub orchestrator_port: u16,
    pub router_port: u16,
    pub reasoning_port: u16,
    pub audit_port: u16,
    pub router_model: String,
    pub reasoning_model: String,
    pub audit_model: String,
    pub max_context_tokens: usize,
    pub llm_host: String,
    /// Separate host for reasoning engine (enables sharing DeepSeek R1 across services).
    /// When set, reasoning calls go to reasoning_host:reasoning_port instead of llm_host:reasoning_port.
    pub reasoning_host: Option<String>,
}

impl Config {
    pub fn from_env() -> Self {
        let reasoning_host = env::var("REASONING_HOST").ok();
        let reasoning_port = env_u16("REASONING_PORT", 4002);

        // Log shared-mode detection
        if reasoning_port == 11435 || reasoning_host.is_some() {
            tracing::info!(
                "Shared reasoning mode: {}:{}",
                reasoning_host.as_deref().unwrap_or("127.0.0.1"),
                reasoning_port
            );
        }

        Self {
            orchestrator_port: env_u16("ORCHESTRATOR_PORT", 8080),
            router_port: env_u16("ROUTER_PORT", 4001),
            reasoning_port,
            audit_port: env_u16("AUDIT_PORT", 4003),
            router_model: env_str("ROUTER_MODEL", "qwen3.6-35b"),
            reasoning_model: env_str("REASONING_MODEL", "qwen3.6-35b"),
            audit_model: env_str("AUDIT_MODEL", "qwen3.5-4b"),
            max_context_tokens: env_usize("MAX_CONTEXT_TOKENS", 8192),
            llm_host: env_str("LLM_HOST", "127.0.0.1"),
            reasoning_host,
        }
    }

    /// Get the effective host for reasoning calls.
    /// Uses REASONING_HOST if set, otherwise falls back to LLM_HOST.
    pub fn reasoning_endpoint(&self) -> (&str, u16) {
        let host = self.reasoning_host.as_deref().unwrap_or(&self.llm_host);
        (host, self.reasoning_port)
    }
}

fn env_str(key: &str, default: &str) -> String {
    env::var(key).unwrap_or_else(|_| default.to_string())
}

fn env_u16(key: &str, default: u16) -> u16 {
    env::var(key)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}

fn env_usize(key: &str, default: usize) -> usize {
    env::var(key)
        .ok()
        .and_then(|v| v.parse().ok())
        .unwrap_or(default)
}
