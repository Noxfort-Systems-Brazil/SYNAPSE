# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Hardware and CUDA/TensorCore initialization routines.
"""

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


__all__ = ["configure_hardware_acceleration"]
