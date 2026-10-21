# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from typing import Optional


def get_project_root() -> str:
    """Returns the absolute root directory of the SYNAPSE project."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_model_vault_dir() -> str:
    """Returns the absolute path to the Model_Vault directory."""
    root = get_project_root()
    return os.path.join(root, "Model_Vault")


def get_modernbert_path() -> str:
    """Returns the unified local path for ModernBERT in Model_Vault."""
    vault = get_model_vault_dir()
    modern_path = os.path.join(vault, "modernbert")
    if os.path.exists(modern_path):
        return modern_path
        
    return "answerdotai/ModernBERT-base"


def get_distilroberta_path() -> str:
    """Backward-compatible alias pointing to modernbert."""
    return get_modernbert_path()


def get_distilroberta_v1_path() -> str:
    """Backward-compatible alias for legacy DistilRoBERTa path."""
    return get_modernbert_path()


def get_distilroberta_base_path() -> str:
    """Backward-compatible alias for legacy DistilRoBERTa path."""
    return get_modernbert_path()


def get_qwen_gguf_path() -> str:
    """Returns the local path to the Qwen GGUF model in Model_Vault."""
    vault = get_model_vault_dir()
    qwen_gguf = os.path.join(vault, "Qwen3.5-2B-UD-Q6_K_XL.gguf")
    return qwen_gguf
