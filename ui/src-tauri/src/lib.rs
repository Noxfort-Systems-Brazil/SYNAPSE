// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

pub mod backend;
pub mod commands;
pub mod services;
pub mod tray;
pub mod utils;

use backend::ipc::send_synapse_command;
use backend::{spawn_python_backend, PythonProcessState};
use commands::dialog::{pick_directory_dialog, pick_file_dialog, save_file_dialog, write_file_bytes};
use commands::window::{minimize_to_tray, restore_from_tray, toggle_fullscreen};
use tauri::{Manager, WindowEvent};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let proc_state = PythonProcessState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.unminimize();
                let _ = window.set_focus();
            }
        }))
        .manage(proc_state)
        .setup(|app| {
            let handle = app.handle().clone();
            let state = app.state::<PythonProcessState>();
            spawn_python_backend(handle, &state);
            tray::setup_tray(app)?;
            Ok(())
        })
        .on_window_event(|window, event| match event {
            WindowEvent::CloseRequested { api, .. } => {
                api.prevent_close();
                let _ = window.hide();
            }
            _ => {}
        })
        .invoke_handler(tauri::generate_handler![
            send_synapse_command,
            pick_file_dialog,
            save_file_dialog,
            pick_directory_dialog,
            write_file_bytes,
            toggle_fullscreen,
            minimize_to_tray,
            restore_from_tray
        ])

        .run(tauri::generate_context!())
        .expect("Error while running Tauri application");
}
