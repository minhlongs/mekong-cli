mod commands;

use tauri::{Emitter, Manager};

/// Tauri application setup and run.
/// Registers all IPC commands grouped by module.
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                window.show().unwrap_or_default();
                window.set_focus().unwrap_or_default();
            }

            // Background task: update tray LLM status every 30 s
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                loop {
                    let status = commands::llm::check_llm_health().await;
                    if let Ok(s) = status {
                        let _label = if s.mlx.online || s.ollama.online {
                            "LLM: Connected"
                        } else {
                            "LLM: Offline"
                        };
                        // Tray update hook — extend in phase-04 when tray is wired
                        let _ = app_handle.emit("llm-status", &_label);
                    }
                    tokio::time::sleep(std::time::Duration::from_secs(30)).await;
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Legacy / example
            greet,
            get_version,
            // LLM
            commands::llm::check_llm_health,
            commands::llm::check_gateway_health,
            commands::llm::chat_completion,
            // Filesystem
            commands::filesystem::read_workspace,
            commands::filesystem::read_file,
            // System
            commands::system::get_system_info,
            commands::system::list_tenants,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Mekong IDE");
}

// ── Keep existing example commands ───────────────────────────────────────────

/// Greet command — kept for backwards compatibility with existing tests.
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! Mekong IDE is running.", name)
}

/// Return the crate version string.
#[tauri::command]
fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
