# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Tuple
from src.utils.logging_setup import get_logger

logger = get_logger("SLM.DeviceManager")


class SLMDeviceManager:
    """
    Handles hardware capability detection, CUDA availability checks, 
    free VRAM evaluation, and offload layer calculations for on-demand GGUF model execution.
    Adheres to the CARINA SLM architecture pattern.
    """

    @staticmethod
    def resolve_device_settings(device: str = "auto", gpu_layers: int = 16) -> Tuple[str, int]:
        """
        Determines the device execution setting ("gpu" vs "cpu") and number of GPU offload layers.
        Returns: (resolved_device_setting, resolved_gpu_layers)
        """
        if device in ("gpu", "cpu", "mixed"):
            device_setting = device
            resolved_layers = gpu_layers if device == "mixed" else (-1 if device == "gpu" else 0)
            logger.info(f"[SLMDeviceManager] Using explicit setting: {device_setting} (gpu_layers={resolved_layers})")

            if device_setting in ("gpu", "mixed"):
                try:
                    import torch
                    if not torch.cuda.is_available():
                        logger.warning("[SLMDeviceManager] GPU requested but CUDA is not available. Falling back to CPU.")
                        return "cpu", 0
                except Exception as e:
                    logger.warning(f"[SLMDeviceManager] Failed CUDA check: {e}. Falling back to CPU.")
                    return "cpu", 0
            return device_setting, resolved_layers

        # Automatic detection based on available VRAM
        try:
            import torch
            if torch.cuda.is_available():
                try:
                    free_vram, total_vram = torch.cuda.mem_get_info()
                    free_vram_gb = free_vram / (1024 ** 3)
                    total_vram_gb = total_vram / (1024 ** 3)
                    logger.info(
                        f"[SLMDeviceManager] CUDA detected. Free VRAM: {free_vram_gb:.2f} GB / Total: {total_vram_gb:.2f} GB"
                    )
                    if free_vram_gb >= 2.5:
                        logger.info("[SLMDeviceManager] Sufficient VRAM detected (>= 2.5GB). Offloading to GPU (-1 layers).")
                        return "gpu", -1
                    else:
                        logger.info("[SLMDeviceManager] Low VRAM detected (< 2.5GB). Running on CPU.")
                        return "cpu", 0
                except Exception as e:
                    logger.warning(f"[SLMDeviceManager] Error checking VRAM: {e}. Using GPU fallback.")
                    return "gpu", -1
            else:
                logger.info("[SLMDeviceManager] CUDA not available. Running on CPU.")
                return "cpu", 0
        except Exception as e:
            logger.warning(f"[SLMDeviceManager] Torch check failed: {e}. Running on CPU.")
            return "cpu", 0
