// Mekong IDE — Tauri shell library
// Command stubs live here; expand post-launch as native IPC needs grow.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![])
        .run(tauri::generate_context!())
        .expect("error while running Mekong IDE");
}
