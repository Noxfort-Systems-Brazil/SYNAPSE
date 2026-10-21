// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

use std::process::{Child, ChildStdin};
use std::sync::{Arc, Mutex};

#[derive(Clone)]
pub struct PythonProcessState {
    pub stdin: Arc<Mutex<Option<ChildStdin>>>,
    pub process: Arc<Mutex<Option<Child>>>,
}

impl PythonProcessState {
    pub fn new() -> Self {
        Self {
            stdin: Arc::new(Mutex::new(None)),
            process: Arc::new(Mutex::new(None)),
        }
    }
}

impl Default for PythonProcessState {
    fn default() -> Self {
        Self::new()
    }
}
