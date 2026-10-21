# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
OS Dialog & Network Info Command Handler (SOLID: SRP & DIP).

Translates IPC actions related to native file picker dialogs and network interface queries.
"""

from typing import Any, Dict, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.infrastructure.dialog_service import NativeDialogService
from src.infrastructure.network_service import NetworkService


class SystemDialogHandler:
    """Handles OS dialogs and network diagnostics."""

    def __init__(
        self,
        dialog_service: Optional[NativeDialogService] = None,
        network_service: Optional[NetworkService] = None,
    ):
        self.dialog_service = dialog_service or NativeDialogService()
        self.network_service = network_service or NetworkService()

    def handle_pick_file(self, msg: IpcMessage) -> Dict[str, Any]:
        title = msg.payload.get("title", "Selecionar Arquivo")
        filter_str = msg.payload.get("filter", "*")
        selected_path = self.dialog_service.pick_file(title, filter_str)
        return {"path": selected_path, "cancelled": selected_path is None}

    def handle_save_file(self, msg: IpcMessage) -> Dict[str, Any]:
        title = msg.payload.get("title", "Salvar Arquivo")
        default_filename = msg.payload.get("default_filename")
        filter_str = msg.payload.get("filter", "*")
        selected_path = self.dialog_service.save_file(default_filename, title, filter_str)
        return {"path": selected_path, "cancelled": selected_path is None}

    def handle_pick_directory(self, msg: IpcMessage) -> Dict[str, Any]:
        title = msg.payload.get("title", "Selecionar Pasta")
        selected_path = self.dialog_service.pick_directory(title)
        return {"path": selected_path, "cancelled": selected_path is None}

    def handle_get_network_info(self, msg: IpcMessage) -> Dict[str, Any]:
        return self.network_service.get_network_info()

