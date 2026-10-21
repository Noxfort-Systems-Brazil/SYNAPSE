# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Native Operating System Dialog Service (SOLID: SRP & DIP).

Isolates OS-specific GUI dialogs (Zenity subprocess and Tkinter fallback)
away from the IPC transport and core domain logic.
"""

import os
import sys
import subprocess
from urllib.parse import unquote, urlparse
from typing import Optional

from src.logging.facade import get_logger


class NativeDialogService:
    """Provides platform-native file and folder selection dialogs."""

    def __init__(self):
        self.logger = get_logger("NativeDialogService")

    def pick_file(
        self, title: str = "Selecionar Arquivo", file_filter: str = "*"
    ) -> Optional[str]:
        """
        Opens a native OS file dialog using zenity (on Linux) or Tkinter fallback.
        """
        self.logger.info(f"📂 [NativeDialogService] Abrindo seletor de arquivos. Título: '{title}' | Filtro: '{file_filter}'")

        if sys.platform.startswith("linux"):
            try:
                cmd = ["zenity", "--file-selection", f"--title={title}"]
                if file_filter and file_filter != "*":
                    cmd.append(f"--file-filter={file_filter}")

                self.logger.debug(f"[NativeDialogService] Executando Zenity: {' '.join(cmd)}")
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    path = res.stdout.strip()
                    if path:
                        if path.startswith("file://"):
                            path = unquote(urlparse(path).path)
                        path = unquote(path)
                        if os.path.exists(path):
                            self.logger.info(f"✅ [NativeDialogService] Arquivo selecionado via Zenity: '{path}'")
                            return path
                        else:
                            self.logger.warning(f"⚠️ [NativeDialogService] Arquivo retornado não existe: '{path}'")
                elif res.returncode == 1:
                    # User cancelled
                    self.logger.info("ℹ️ [NativeDialogService] Seleção cancelada pelo usuário no Zenity.")
                    return None
                else:
                    self.logger.warning(f"⚠️ [NativeDialogService] Zenity retornou código {res.returncode}: {res.stderr}")
            except Exception as ex:
                self.logger.warning(f"⚠️ [NativeDialogService] Erro no Zenity: {ex}. Tentando fallback Tkinter...")

        # Fallback to Tkinter file picker dialog
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            # Build Tkinter filetypes list if filter provided
            filetypes = []
            if file_filter and "|" in file_filter:
                parts = file_filter.split("|")
                desc = parts[0].strip()
                patterns = parts[1].strip()
                filetypes.append((desc, patterns))
            elif file_filter and file_filter != "*":
                filetypes.append(("Arquivos Filtrados", file_filter))
            else:
                filetypes.append(("Todos os Arquivos", "*.*"))

            self.logger.debug(f"[NativeDialogService] Abrindo Tkinter filedialog com filetypes: {filetypes}")
            selected = filedialog.askopenfilename(title=title, filetypes=filetypes)
            root.destroy()
            if selected:
                if selected.startswith("file://"):
                    selected = unquote(urlparse(selected).path)
                selected = unquote(selected)
                if os.path.exists(selected):
                    self.logger.info(f"✅ [NativeDialogService] Arquivo selecionado via Tkinter: '{selected}'")
                    return selected
                else:
                    self.logger.warning(f"⚠️ [NativeDialogService] Arquivo retornado não existe: '{selected}'")
            else:
                self.logger.info("ℹ️ [NativeDialogService] Seleção cancelada no Tkinter.")
        except Exception as ex:
            self.logger.error(f"❌ [NativeDialogService] Erro no seletor Tkinter: {ex}", exc_info=True)

        return None

    def save_file(
        self,
        default_filename: Optional[str] = None,
        title: str = "Salvar Arquivo",
        file_filter: str = "*",
    ) -> Optional[str]:
        """
        Opens a native OS save file dialog using zenity (on Linux) or Tkinter fallback.
        """
        self.logger.info(
            f"💾 [NativeDialogService] Abrindo diálogo de salvar arquivo. Título: '{title}' | Padrão: '{default_filename}' | Filtro: '{file_filter}'"
        )

        if sys.platform.startswith("linux"):
            try:
                cmd = ["zenity", "--file-selection", "--save", "--confirm-overwrite", f"--title={title}"]
                if default_filename:
                    cmd.append(f"--filename={default_filename}")
                if file_filter and file_filter != "*":
                    cmd.append(f"--file-filter={file_filter}")

                self.logger.debug(f"[NativeDialogService] Executando Zenity Save: {' '.join(cmd)}")
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    path = res.stdout.strip()
                    if path:
                        if path.startswith("file://"):
                            path = unquote(urlparse(path).path)
                        path = unquote(path)
                        self.logger.info(f"✅ [NativeDialogService] Destino selecionado via Zenity: '{path}'")
                        return path
                elif res.returncode == 1:
                    self.logger.info("ℹ️ [NativeDialogService] Salvamento cancelado pelo usuário no Zenity.")
                    return None
                else:
                    self.logger.warning(f"⚠️ [NativeDialogService] Zenity retornou código {res.returncode}: {res.stderr}")
            except Exception as ex:
                self.logger.warning(f"⚠️ [NativeDialogService] Erro no Zenity save: {ex}. Tentando fallback Tkinter...")

        # Fallback to Tkinter file save dialog
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)

            filetypes = []
            if file_filter and "|" in file_filter:
                parts = file_filter.split("|")
                desc = parts[0].strip()
                patterns = parts[1].strip()
                filetypes.append((desc, patterns))
            elif file_filter and file_filter != "*":
                filetypes.append(("Arquivos Filtrados", file_filter))
            else:
                filetypes.append(("Todos os Arquivos", "*.*"))

            selected = filedialog.asksaveasfilename(
                title=title,
                initialfile=default_filename,
                filetypes=filetypes,
            )
            root.destroy()
            if selected:
                if selected.startswith("file://"):
                    selected = unquote(urlparse(selected).path)
                selected = unquote(selected)
                self.logger.info(f"✅ [NativeDialogService] Destino selecionado via Tkinter: '{selected}'")
                return selected
            else:
                self.logger.info("ℹ️ [NativeDialogService] Salvamento cancelado no Tkinter.")
        except Exception as ex:
            self.logger.error(f"❌ [NativeDialogService] Erro no diálogo de salvar Tkinter: {ex}", exc_info=True)

        return None

    def pick_directory(self, title: str = "Selecionar Pasta") -> Optional[str]:
        """
        Opens a native OS folder picker dialog using zenity (on Linux) or Tkinter fallback.
        """
        self.logger.info(f"📁 [NativeDialogService] Abrindo seletor de pasta. Título: '{title}'")

        if sys.platform.startswith("linux"):
            try:
                cmd = ["zenity", "--file-selection", "--directory", f"--title={title}"]
                self.logger.debug(f"[NativeDialogService] Executando Zenity Directory: {' '.join(cmd)}")
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                if res.returncode == 0:
                    path = res.stdout.strip()
                    if path:
                        if path.startswith("file://"):
                            path = unquote(urlparse(path).path)
                        path = unquote(path)
                        if os.path.isdir(path):
                            self.logger.info(f"✅ [NativeDialogService] Pasta selecionada via Zenity: '{path}'")
                            return path
                elif res.returncode == 1:
                    self.logger.info("ℹ️ [NativeDialogService] Seleção de pasta cancelada pelo usuário no Zenity.")
                    return None
            except Exception as ex:
                self.logger.warning(f"⚠️ [NativeDialogService] Erro no Zenity directory: {ex}. Tentando fallback Tkinter...")

        # Fallback to Tkinter directory picker
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askdirectory(title=title)
            root.destroy()
            if selected:
                if selected.startswith("file://"):
                    selected = unquote(urlparse(selected).path)
                selected = unquote(selected)
                if os.path.isdir(selected):
                    self.logger.info(f"✅ [NativeDialogService] Pasta selecionada via Tkinter: '{selected}'")
                    return selected
            else:
                self.logger.info("ℹ️ [NativeDialogService] Seleção de pasta cancelada no Tkinter.")
        except Exception as ex:
            self.logger.error(f"❌ [NativeDialogService] Erro no seletor de pasta Tkinter: {ex}", exc_info=True)

        return None

