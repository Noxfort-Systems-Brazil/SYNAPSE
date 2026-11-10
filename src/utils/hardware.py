# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Hardware, AMP dtype (BF16/FP16), and Torch Inductor compilation routines.
"""

import logging
import os
from typing import Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import torch

logger = logging.getLogger(__name__)


def configure_hardware_acceleration() -> None:
    """
    Global Hardware Acceleration & Tensor Core Configuration:
    - RTX 20xx Series (Turing CC 7.5): Optimizes cuDNN benchmarking to select the fastest
      FP16 Tensor Core kernels for convolutions and matrix operations.
    - RTX 30xx/40xx/50xx Series (Ampere / Ada / Hopper / Blackwell CC >= 8.0):
      Enables TensorFloat-32 (TF32) and high float32 matmul precision for transparent acceleration.
    """
    try:
        import torch
        if torch.cuda.is_available():
            torch.set_float32_matmul_precision('high')
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
    except Exception:
        pass


def get_optimal_amp_dtype(device: Union["torch.device", str]) -> "torch.dtype":
    """
    Selects the optimal Automatic Mixed Precision dtype for the target device:
    - CUDA with native BF16 support (Ampere CC >= 8.0): torch.bfloat16 (prevents PDE residual underflow).
    - CUDA without BF16 support (Turing CC 7.5): torch.float16.
    - CPU / MPS: torch.float32.
    """
    import torch

    dev = torch.device(device) if isinstance(device, str) else device
    if dev.type == "cuda":
        try:
            if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
                return torch.bfloat16
        except Exception:
            pass
        return torch.float16
    return torch.float32


def requires_grad_scaler(
    device: Union["torch.device", str],
    amp_dtype: Optional["torch.dtype"] = None,
) -> bool:
    """
    Returns True only when GradScaler is numerically required (CUDA + float16).
    bfloat16 shares the 8-bit exponent dynamic range of float32 and does not require scaling.
    """
    import torch

    dev = torch.device(device) if isinstance(device, str) else device
    if dev.type != "cuda":
        return False
    dtype = amp_dtype if amp_dtype is not None else get_optimal_amp_dtype(dev)
    return dtype == torch.float16


def maybe_compile_module(
    module: "torch.nn.Module",
    device: Optional[Union["torch.device", str]] = None,
    dynamic: bool = True,
    mode: str = "default",
) -> "torch.nn.Module":
    """
    Safely applies in-place PyTorch 2.x `module.compile(...)` on pure-PyTorch backbones.
    In-place compilation preserves `isinstance(module, Cls)` and original `state_dict()` keys.

    Controlled via `SYNAPSE_TORCH_COMPILE`:
    - "0" / "false" / "off": Disabled.
    - "1" / "true" / "on": Enabled on the active device.
    - "auto" (default): Enabled automatically when targeting a CUDA GPU.
    """
    import torch

    env_flag = os.environ.get("SYNAPSE_TORCH_COMPILE", "auto").strip().lower()
    if env_flag in ("0", "false", "off", "no"):
        return module

    if device is not None:
        dev = torch.device(device) if isinstance(device, str) else device
    else:
        try:
            dev = next(module.parameters()).device
        except StopIteration:
            dev = torch.device("cpu")

    should_compile = (env_flag in ("1", "true", "on", "yes")) or (
        env_flag == "auto" and dev.type == "cuda" and torch.cuda.is_available()
    )
    if not should_compile:
        return module

    compile_fn = getattr(module, "compile", None)
    if callable(compile_fn):
        try:
            compile_fn(dynamic=dynamic, mode=mode)
            setattr(module, "_synapse_compiled", True)
            logger.info(
                f"[Hardware] In-place torch.compile(dynamic={dynamic}, mode='{mode}') enabled for {module.__class__.__name__}."
            )
        except Exception as exc:
            logger.debug(f"[Hardware] Skipping torch.compile for {module.__class__.__name__}: {exc}")

    return module


__all__ = [
    "configure_hardware_acceleration",
    "get_optimal_amp_dtype",
    "requires_grad_scaler",
    "maybe_compile_module",
]
