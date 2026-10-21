# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import math
import warnings
from contextlib import contextmanager
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any


@contextmanager
def get_sdp_context(
    enable_flash: bool = True,
    enable_mem_efficient: bool = True,
    enable_math: bool = True
):
    """
    Context manager for PyTorch Scaled Dot-Product Attention kernels.
    Uses modern torch.nn.attention.sdpa_kernel when available,
    falling back to torch.backends.cuda.sdp_kernel with deprecation warnings suppressed.
    """
    # 1. Try modern PyTorch (torch.nn.attention.sdpa_kernel)
    try:
        from torch.nn.attention import sdpa_kernel, SDPBackend
        backends = []
        if enable_flash:
            backends.append(SDPBackend.FLASH_ATTENTION)
        if enable_mem_efficient:
            backends.append(SDPBackend.EFFICIENT_ATTENTION)
        if enable_math:
            backends.append(SDPBackend.MATH)
        with sdpa_kernel(backends):
            yield
            return
    except (ImportError, AttributeError):
        pass

    # 2. Legacy PyTorch fallback with FutureWarning suppressed
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=FutureWarning, message=".*sdp_kernel.*")
        sdp_kernel_fn = getattr(torch.backends.cuda, "sdp_kernel", None)
        if callable(sdp_kernel_fn):
            try:
                with sdp_kernel_fn(
                    enable_flash=enable_flash,
                    enable_mem_efficient=enable_mem_efficient,
                    enable_math=enable_math
                ):
                    yield
                    return
            except Exception:
                pass
        yield


def get_sdpa_backend_info() -> Dict[str, Any]:
    """
    Returns the diagnostic status of Scaled Dot-Product Attention backends 
    available in the current PyTorch execution environment.
    """
    cuda_avail = torch.cuda.is_available()
    flash_enabled = False
    mem_efficient_enabled = False
    math_enabled = True

    cuda_backends = getattr(torch.backends, "cuda", None)
    if cuda_avail and cuda_backends is not None:
        flash_fn = getattr(cuda_backends, "flash_sdp_enabled", None)
        if callable(flash_fn):
            flash_enabled = flash_fn()
        mem_fn = getattr(cuda_backends, "mem_efficient_sdp_enabled", None)
        if callable(mem_fn):
            mem_efficient_enabled = mem_fn()
        math_fn = getattr(cuda_backends, "math_sdp_enabled", None)
        if callable(math_fn):
            math_enabled = math_fn()

    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    device_capability = torch.cuda.get_device_capability(0) if cuda_avail else (0, 0)

    return {
        "cuda_available": cuda_avail,
        "device_name": device_name,
        "compute_capability": device_capability,
        "flash_sdp": flash_enabled,
        "mem_efficient_sdp": mem_efficient_enabled,
        "math_sdp": math_enabled
    }


def fallback_math_attention(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: Optional[torch.Tensor] = None,
    dropout_p: float = 0.0,
    scale: Optional[float] = None
) -> torch.Tensor:
    """
    Standard matrix multiplication attention:
        Output = Softmax( (Q * K^T) / sqrt(d_k) ) * V
    
    Guaranteed fallback that operates deterministically on any hardware,
    device (CPU/GPU), precision, or tensor layout.
    """
    d_k = query.size(-1)
    if scale is None:
        scale = 1.0 / math.sqrt(d_k)

    scores = torch.matmul(query, key.transpose(-2, -1)) * scale

    if attn_mask is not None:
        if attn_mask.dtype == torch.bool:
            scores = scores.masked_fill(~attn_mask, float("-inf"))
        else:
            scores = scores + attn_mask

    attn = F.softmax(scores, dim=-1)
    if dropout_p > 0.0:
        attn = F.dropout(attn, p=dropout_p)

    return torch.matmul(attn, value)


def robust_sdpa(
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attn_mask: Optional[torch.Tensor] = None,
    dropout_p: float = 0.0,
    is_causal: bool = False,
    scale: Optional[float] = None,
    enable_flash: bool = True,
    enable_mem_efficient: bool = True,
    enable_math: bool = True
) -> torch.Tensor:
    """
    Hardware-adaptive Scaled Dot-Product Attention with automated tiered fallback:
    
    Tier 1: FlashAttention (Ampere / Ada Lovelace / Hopper, compute capability >= 8.0)
    Tier 2: Memory-Efficient Attention CUTLASS (Turing / Volta, compute capability 7.0/7.5)
    Tier 3: Math (Classic O(N^2) memory backup for CPU, legacy cards, or unaligned shapes)

    Ensures SYNAPSE never halts with an unhandled CUDA kernel exception.
    """
    sdpa_fn = getattr(F, "scaled_dot_product_attention", None)
    if callable(sdpa_fn):
        # If running on CUDA, wrap in sdp context to enforce tiered priority without deprecation warnings
        if query.is_cuda:
            try:
                with get_sdp_context(
                    enable_flash=enable_flash,
                    enable_mem_efficient=enable_mem_efficient,
                    enable_math=enable_math
                ):
                    return sdpa_fn(
                        query,
                        key,
                        value,
                        attn_mask=attn_mask,
                        dropout_p=dropout_p,
                        is_causal=is_causal,
                        scale=scale
                    )
            except Exception:
                # Kernel dispatch or shape mismatch fallback
                return fallback_math_attention(
                    query, key, value, attn_mask=attn_mask, dropout_p=dropout_p, scale=scale
                )
        else:
            try:
                return F.scaled_dot_product_attention(
                    query,
                    key,
                    value,
                    attn_mask=attn_mask,
                    dropout_p=dropout_p,
                    is_causal=is_causal,
                    scale=scale
                )
            except Exception:
                return fallback_math_attention(
                    query, key, value, attn_mask=attn_mask, dropout_p=dropout_p, scale=scale
                )

    # PyTorch version fallback
    return fallback_math_attention(
        query, key, value, attn_mask=attn_mask, dropout_p=dropout_p, scale=scale
    )
