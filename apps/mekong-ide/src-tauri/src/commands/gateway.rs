//! Generic gateway HTTP proxy — lets the frontend call any gateway endpoint
//! via Tauri IPC, bypassing WebView sandbox restrictions.

use serde_json::Value;

const GATEWAY_BASE: &str = "http://localhost:8000";

/// Proxy any HTTP request to the local gateway.
/// Frontend calls: invoke("gateway_fetch", { path: "/v1/tenants", method: "GET" })
#[tauri::command]
pub async fn gateway_fetch(
    path: String,
    method: String,
    body: Option<String>,
) -> Result<Value, String> {
    let url = format!("{}{}", GATEWAY_BASE, path);
    let client = reqwest::Client::new();

    let req = match method.to_uppercase().as_str() {
        "GET" => client.get(&url),
        "POST" => {
            let mut r = client.post(&url);
            if let Some(b) = &body {
                r = r.header("Content-Type", "application/json").body(b.clone());
            }
            r
        }
        "PATCH" => {
            let mut r = client.patch(&url);
            if let Some(b) = &body {
                r = r.header("Content-Type", "application/json").body(b.clone());
            }
            r
        }
        "DELETE" => client.delete(&url),
        _ => return Err(format!("Unsupported method: {}", method)),
    };

    let resp = req
        .timeout(std::time::Duration::from_secs(30))
        .send()
        .await
        .map_err(|e| format!("fetch error: {}", e))?;

    if !resp.status().is_success() {
        let status = resp.status().as_u16();
        let text = resp.text().await.unwrap_or_default();
        return Err(format!("HTTP {}: {}", status, text));
    }

    let json: Value = resp
        .json()
        .await
        .map_err(|e| format!("parse error: {}", e))?;

    Ok(json)
}
