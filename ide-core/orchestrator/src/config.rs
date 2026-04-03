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
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            orchestrator_port: env_u16("ORCHESTRATOR_PORT", 8080),
            router_port: env_u16("ROUTER_PORT", 4001),
            reasoning_port: env_u16("REASONING_PORT", 4002),
            audit_port: env_u16("AUDIT_PORT", 4003),
            router_model: env_str("ROUTER_MODEL", "gemma-4-26b-a4b"),
            reasoning_model: env_str("REASONING_MODEL", "deepseek-r1-32b"),
            audit_model: env_str("AUDIT_MODEL", "qwen2.5-coder-7b"),
            max_context_tokens: env_usize("MAX_CONTEXT_TOKENS", 8192),
            llm_host: env_str("LLM_HOST", "127.0.0.1"),
        }
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
