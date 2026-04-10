/// System tray icon and menu for Mekong IDE.
///
/// Creates a macOS-style system tray with:
/// - Show/hide window toggle on left click
/// - Context menu: Show Window, LLM Status, Quit
/// - LLM status updatable at runtime via `update_llm_status`
use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, Runtime,
};

/// Build and attach the system tray icon to the app.
///
/// Call once inside `tauri::Builder::setup()`.
pub fn setup_tray<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "Show Mekong IDE", true, None::<&str>)?;
    let sep1 = tauri::menu::PredefinedMenuItem::separator(app)?;
    let status = MenuItem::with_id(
        app,
        "llm_status",
        "LLM Status: Checking...",
        false,
        None::<&str>,
    )?;
    let sep2 = tauri::menu::PredefinedMenuItem::separator(app)?;
    let quit = MenuItem::with_id(app, "quit", "Quit Mekong IDE", true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&show, &sep1, &status, &sep2, &quit])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        // Don't show menu on left-click; handle show/hide instead
        .menu_on_left_click(false)
        .tooltip("Mekong IDE")
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                show_main_window(app);
            }
            "quit" => {
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            // Left-click on tray icon → toggle window visibility
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                toggle_main_window(app);
            }
        })
        .build(app)?;

    Ok(())
}

/// Show and focus the main window.
fn show_main_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.show();
        let _ = window.set_focus();
        // Un-minimize if minimized
        let _ = window.unminimize();
    }
}

/// Toggle main window visibility.
/// Shows if hidden/minimized, hides if currently visible and focused.
fn toggle_main_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(window) = app.get_webview_window("main") {
        let is_visible = window.is_visible().unwrap_or(false);
        let is_minimized = window.is_minimized().unwrap_or(false);

        if is_visible && !is_minimized {
            let _ = window.hide();
        } else {
            show_main_window(app);
        }
    }
}

/// Update the "LLM Status" tray menu item text at runtime.
///
/// # Arguments
/// * `app`    - App handle (available from commands or events)
/// * `status` - Short status string, e.g. "Connected", "Offline", "claude-opus-4"
pub fn update_llm_status<R: Runtime>(app: &AppHandle<R>, status: &str) {
    // Tauri v2: iterate tray icons and update menu item text
    let label = format!("LLM: {}", status);
    for tray in app.tray_icon_list() {
        if let Some(menu) = tray.menu() {
            // Find the item by id and update its text
            if let Some(item) = menu.get("llm_status") {
                if let Some(mi) = item.as_menuitem() {
                    let _ = mi.set_text(&label);
                }
            }
        }
    }
}
