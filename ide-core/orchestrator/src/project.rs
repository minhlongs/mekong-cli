use std::path::Path;

const PROJECT_FILE: &str = "MEKONG.md";

/// Load project-level instructions from MEKONG.md (or CLAUDE.md fallback).
/// Equivalent to Claude Code's CLAUDE.md auto-loading.
pub fn load_project_context(workspace: &str) -> Option<String> {
    let path = Path::new(workspace).join(PROJECT_FILE);
    match std::fs::read_to_string(&path) {
        Ok(content) => {
            tracing::info!("Loaded {} ({} bytes)", PROJECT_FILE, content.len());
            Some(format!(
                "# Project Instructions (from {})\n\n{}\n\n---\n",
                PROJECT_FILE, content
            ))
        }
        Err(_) => {
            // Fallback to CLAUDE.md
            let fallback = Path::new(workspace).join("CLAUDE.md");
            match std::fs::read_to_string(&fallback) {
                Ok(content) => {
                    tracing::info!("Loaded CLAUDE.md fallback ({} bytes)", content.len());
                    Some(format!(
                        "# Project Instructions (from CLAUDE.md)\n\n{}\n\n---\n",
                        content
                    ))
                }
                Err(_) => None,
            }
        }
    }
}
