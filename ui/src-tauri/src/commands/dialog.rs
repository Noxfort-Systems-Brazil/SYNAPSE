// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

use std::fs;
use std::io::Write;
use crate::services::dialog_service::{DialogGuard, DialogService};
use crate::utils::base64::decode_base64;

#[tauri::command]
pub async fn pick_file_dialog(
    title: Option<String>,
    filter_name: Option<String>,
    filter_extensions: Option<Vec<String>>,
) -> Result<Option<String>, String> {
    let _guard = match DialogGuard::try_acquire() {
        Some(g) => g,
        None => {
            eprintln!("[Tauri] pick_file_dialog ignorado: um diálogo de arquivo já está ativo.");
            return Ok(None);
        }
    };

    tokio::task::spawn_blocking(move || {
        DialogService::open_file(title, filter_name, filter_extensions)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn save_file_dialog(
    default_filename: Option<String>,
    title: Option<String>,
    filter_name: Option<String>,
    filter_extensions: Option<Vec<String>>,
) -> Result<Option<String>, String> {
    let _guard = match DialogGuard::try_acquire() {
        Some(g) => g,
        None => {
            eprintln!("[Tauri] save_file_dialog ignorado: um diálogo de arquivo já está ativo.");
            return Ok(None);
        }
    };

    tokio::task::spawn_blocking(move || {
        DialogService::save_file(default_filename, title, filter_name, filter_extensions)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn write_file_bytes(file_path: String, base64_content: String) -> Result<(), String> {
    tokio::task::spawn_blocking(move || {
        let bytes = decode_base64(&base64_content)
            .map_err(|e| format!("Base64 decoding error: {}", e))?;
        let mut file = fs::File::create(&file_path).map_err(|e| e.to_string())?;
        file.write_all(&bytes).map_err(|e| e.to_string())?;
        Ok(())
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn pick_directory_dialog(title: Option<String>) -> Result<Option<String>, String> {
    let _guard = match DialogGuard::try_acquire() {
        Some(g) => g,
        None => {
            eprintln!("[Tauri] pick_directory_dialog ignorado: um diálogo de arquivo já está ativo.");
            return Ok(None);
        }
    };

    tokio::task::spawn_blocking(move || {
        DialogService::pick_directory(title)
    })
    .await
    .map_err(|e| e.to_string())?
}

