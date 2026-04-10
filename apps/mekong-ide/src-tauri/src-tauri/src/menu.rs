/// Native macOS menu bar for Mekong IDE.
///
/// Provides:
/// - App menu: About, Preferences (Cmd+,), Quit (Cmd+Q)
/// - Edit menu: Undo, Redo, Cut, Copy, Paste, Select All
/// - View menu: Reload (Cmd+R), Toggle DevTools (Cmd+Alt+I), Zoom In/Out
/// - Window menu: Minimize (Cmd+M), Close (Cmd+W)
use tauri::{
    menu::{MenuBuilder, PredefinedMenuItem, SubmenuBuilder},
    AppHandle, Manager, Runtime,
};

/// Build and attach the native menu bar to the app.
///
/// Call once inside `tauri::Builder::setup()` after tray setup.
pub fn setup_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let menu = MenuBuilder::new(app)
        .item(&build_app_menu(app)?)
        .item(&build_edit_menu(app)?)
        .item(&build_view_menu(app)?)
        .item(&build_window_menu(app)?)
        .build()?;

    app.set_menu(menu)?;
    Ok(())
}

/// App menu: About, Preferences, Quit
fn build_app_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<tauri::menu::Submenu<R>> {
    SubmenuBuilder::new(app, "Mekong IDE")
        .about(None)
        .separator()
        .item(&PredefinedMenuItem::new(
            app,
            Some("Preferences"),
            Some("preferences"),
        )?)
        .separator()
        .quit()
        .build()
}

/// Edit menu: Undo, Redo, Cut, Copy, Paste, Select All
fn build_edit_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<tauri::menu::Submenu<R>> {
    SubmenuBuilder::new(app, "Edit")
        .undo()
        .redo()
        .separator()
        .cut()
        .copy()
        .paste()
        .select_all()
        .build()
}

/// View menu: Reload, Toggle DevTools, Zoom In/Out
fn build_view_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<tauri::menu::Submenu<R>> {
    let reload =
        tauri::menu::MenuItem::with_id(app, "reload", "Reload", true, Some("CmdOrCtrl+R"))?;
    let devtools = tauri::menu::MenuItem::with_id(
        app,
        "toggle_devtools",
        "Toggle Developer Tools",
        true,
        Some("CmdOrCtrl+Alt+I"),
    )?;
    let zoom_in =
        tauri::menu::MenuItem::with_id(app, "zoom_in", "Zoom In", true, Some("CmdOrCtrl+="))?;
    let zoom_out =
        tauri::menu::MenuItem::with_id(app, "zoom_out", "Zoom Out", true, Some("CmdOrCtrl+-"))?;

    SubmenuBuilder::new(app, "View")
        .item(&reload)
        .item(&devtools)
        .separator()
        .item(&zoom_in)
        .item(&zoom_out)
        .build()
}

/// Window menu: Minimize, Close
fn build_window_menu<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<tauri::menu::Submenu<R>> {
    SubmenuBuilder::new(app, "Window")
        .minimize()
        .close_window()
        .build()
}

/// Handle menu events from the native menu bar.
///
/// Wire this to `tauri::Builder::on_menu_event()` in `lib.rs`.
pub fn handle_menu_event<R: Runtime>(app: &AppHandle<R>, event: &tauri::menu::MenuEvent) {
    match event.id.as_ref() {
        "reload" => {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval("window.location.reload()");
            }
        }
        "toggle_devtools" =>
        {
            #[cfg(debug_assertions)]
            if let Some(window) = app.get_webview_window("main") {
                if window.is_devtools_open() {
                    window.close_devtools();
                } else {
                    window.open_devtools();
                }
            }
        }
        "zoom_in" => {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval(
                    "document.body.style.zoom = (parseFloat(document.body.style.zoom || '1') + 0.1).toString()",
                );
            }
        }
        "zoom_out" => {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.eval(
                    "document.body.style.zoom = Math.max(0.5, parseFloat(document.body.style.zoom || '1') - 0.1).toString()",
                );
            }
        }
        "preferences" => {
            // Emit event to frontend to open preferences panel
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
                let _ = window.emit("menu:preferences", ());
            }
        }
        _ => {}
    }
}
