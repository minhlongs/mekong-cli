/// System-information command: OS, architecture, hostname, memory.
use serde::Serialize;

#[derive(Serialize)]
pub struct SystemInfo {
    pub cpu_arch: String,
    pub os: String,
    pub memory_total_gb: f64,
    pub hostname: String,
}

/// Return static host information for the status panel.
#[tauri::command]
pub fn get_system_info() -> SystemInfo {
    let hostname = hostname::get()
        .map(|h| h.to_string_lossy().to_string())
        .unwrap_or_else(|_| "unknown".to_string());

    // sysinfo: query total physical memory
    let memory_total_gb = {
        use sysinfo::System;
        let mut sys = System::new();
        sys.refresh_memory();
        sys.total_memory() as f64 / 1024.0 / 1024.0 / 1024.0
    };

    SystemInfo {
        cpu_arch: std::env::consts::ARCH.to_string(),
        os: std::env::consts::OS.to_string(),
        memory_total_gb,
        hostname,
    }
}

/// List tenants from the local gateway.
#[tauri::command]
pub async fn list_tenants() -> Result<Vec<serde_json::Value>, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(5))
        .build()
        .map_err(|e| e.to_string())?;

    let resp = client
        .get("http://localhost:8000/v1/tenants")
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if resp.status().is_success() {
        let data: Vec<serde_json::Value> = resp.json().await.map_err(|e| e.to_string())?;
        Ok(data)
    } else {
        Err(format!("Gateway returned {}", resp.status()))
    }
}
