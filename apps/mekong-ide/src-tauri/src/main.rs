// Prevents an additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// Entry point for the Mekong IDE desktop application.
/// Delegates all setup to lib.rs via run().
fn main() {
    mekong_ide_lib::run();
}
