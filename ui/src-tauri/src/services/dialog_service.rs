// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

use std::process::Command;
use std::sync::atomic::{AtomicBool, Ordering};

static IS_DIALOG_ACTIVE: AtomicBool = AtomicBool::new(false);

pub struct DialogGuard;

impl DialogGuard {
    pub fn try_acquire() -> Option<Self> {
        if IS_DIALOG_ACTIVE
            .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
            .is_ok()
        {
            Some(DialogGuard)
        } else {
            None
        }
    }
}

impl Drop for DialogGuard {
    fn drop(&mut self) {
        IS_DIALOG_ACTIVE.store(false, Ordering::SeqCst);
    }
}

pub struct DialogService;

impl DialogService {
    /// Invocates OS native/zenity modal file open dialog.
    pub fn open_file(
        title: Option<String>,
        filter_name: Option<String>,
        filter_extensions: Option<Vec<String>>,
    ) -> Result<Option<String>, String> {
        let mut cmd = Command::new("zenity");
        cmd.arg("--file-selection");
        cmd.arg("--modal");

        if let Some(ref t) = title {
            cmd.arg(format!("--title={}", t));
        }

        if let (Some(ref name), Some(ref exts)) = (filter_name, filter_extensions) {
            let patterns = exts
                .iter()
                .map(|e| format!("*.{}", e.trim_start_matches('.')))
                .collect::<Vec<_>>()
                .join(" ");
            cmd.arg(format!("--file-filter={} | {}", name, patterns));
        }

        match cmd.output() {
            Ok(output) => {
                if output.status.success() {
                    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                    if !path.is_empty() {
                        return Ok(Some(path));
                    }
                }
                Ok(None)
            }
            Err(e) => {
                eprintln!("[DialogService] Zenity open file error: {}", e);
                Err(e.to_string())
            }
        }
    }

    /// Invocates OS native/zenity modal file save dialog.
    pub fn save_file(
        default_filename: Option<String>,
        title: Option<String>,
        filter_name: Option<String>,
        filter_extensions: Option<Vec<String>>,
    ) -> Result<Option<String>, String> {
        let mut cmd = Command::new("zenity");
        cmd.arg("--file-selection");
        cmd.arg("--save");
        cmd.arg("--confirm-overwrite");
        cmd.arg("--modal");

        if let Some(ref t) = title {
            cmd.arg(format!("--title={}", t));
        }

        if let Some(ref f) = default_filename {
            cmd.arg(format!("--filename={}", f));
        }

        let target_ext = filter_extensions
            .as_ref()
            .and_then(|exts| exts.first().map(|s| s.trim_start_matches('.').to_string()))
            .or_else(|| {
                default_filename.as_ref().and_then(|f| {
                    if let Some(pos) = f.rfind('.') {
                        Some(f[pos + 1..].to_string())
                    } else {
                        None
                    }
                })
            });

        if let (Some(ref name), Some(ref exts)) = (filter_name, filter_extensions) {
            let patterns = exts
                .iter()
                .map(|e| format!("*.{}", e.trim_start_matches('.')))
                .collect::<Vec<_>>()
                .join(" ");
            cmd.arg(format!("--file-filter={} | {}", name, patterns));
        }

        match cmd.output() {
            Ok(output) => {
                if output.status.success() {
                    let mut path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                    if !path.is_empty() {
                        if let Some(ref ext) = target_ext {
                            let dot_ext = format!(".{}", ext.to_lowercase());
                            if !path.to_lowercase().ends_with(&dot_ext) {
                                path.push_str(&dot_ext);
                            }
                        }
                        return Ok(Some(path));
                    }
                }
                Ok(None)
            }
            Err(e) => {
                eprintln!("[DialogService] Zenity save file error: {}", e);
                Err(e.to_string())
            }
        }
    }

    /// Invocates OS native/zenity modal directory picker dialog.
    pub fn pick_directory(title: Option<String>) -> Result<Option<String>, String> {
        let mut cmd = Command::new("zenity");
        cmd.arg("--file-selection");
        cmd.arg("--directory");
        cmd.arg("--modal");

        if let Some(ref t) = title {
            cmd.arg(format!("--title={}", t));
        }

        match cmd.output() {
            Ok(output) => {
                if output.status.success() {
                    let path = String::from_utf8_lossy(&output.stdout).trim().to_string();
                    if !path.is_empty() {
                        return Ok(Some(path));
                    }
                }
                Ok(None)
            }
            Err(e) => {
                eprintln!("[DialogService] Zenity pick directory error: {}", e);
                Err(e.to_string())
            }
        }
    }
}

