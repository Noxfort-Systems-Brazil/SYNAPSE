# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
import logging
from typing import Any, Optional
from torch.amp import autocast

from src.models.pi_deeponet import PIDeepONet
from src.utils.hardware import get_optimal_amp_dtype
from src.utils.normalization import TensorNormalizer

logger = logging.getLogger("Synapse.ImputerPipeline")


class ImputerPipeline:
    """
    Dedicated Neural Pipeline for Gap Imputation and Time-Series Reconstruction.
    Encapsulates PIDeepONet chunking, continuous operator evaluation, and Z-Score signal restoration.
    """

    def __init__(
        self,
        model: Optional[PIDeepONet] = None,
        feature_dim: int = 4,
        seq_len: int = 24,
        patch_len: int = 8,
        stride: int = 4,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        d_ff: int = 128,
        dropout: float = 0.1,
        device: Optional[torch.device] = None,
        **kwargs: Any
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.seq_len = seq_len
        self.feature_dim = feature_dim

        if model is not None:
            self.model = model
        else:
            self.model = PIDeepONet(
                feature_dim=feature_dim,
                seq_len=seq_len,
                p_latent=d_model,
                hidden_dim=d_ff,
                dropout=dropout,
                **kwargs
            )

        self.model.to(self.device)

    def to(self, device: Any) -> 'ImputerPipeline':
        self.device = torch.device(device) if isinstance(device, str) else device
        self.model.to(self.device)
        return self

    def reconstruct(self, incomplete_seq: np.ndarray, chunk_size: int = 4096) -> np.ndarray:
        """
        Uses PIDeepONet to reconstruct missing values (NaNs) in multivariate sequences
        via vectorized mini-batches without inner-loop CUDA synchronizations.
        """
        if incomplete_seq.size == 0:
            return incomplete_seq.copy()

        self.model.eval()

        working_seq = incomplete_seq.copy()
        mask = np.isnan(working_seq)
        working_seq[mask] = 0.0  # Zero-fill for numerical stability

        is_2d = (working_seq.ndim == 2)
        working_seq = np.ascontiguousarray(working_seq, dtype=np.float32)

        reconstructed_results = []
        device_type = self.device.type if self.device.type != 'mps' else 'cpu'
        amp_dtype = get_optimal_amp_dtype(self.device)
        use_cuda = (self.device.type == 'cuda')

        with torch.no_grad():
            if is_2d:
                total_length, num_feats = working_seq.shape
                num_full = total_length // self.seq_len
                rem = total_length % self.seq_len

                window_parts = []
                if num_full > 0:
                    full_view = working_seq[: num_full * self.seq_len].reshape(num_full, self.seq_len, num_feats)
                    window_parts.append(full_view)
                if rem > 0:
                    tail = working_seq[num_full * self.seq_len :]
                    pad_rows = self.seq_len - rem
                    tail_padded = np.pad(tail, ((0, pad_rows), (0, 0)), mode='reflect')
                    window_parts.append(tail_padded[np.newaxis, :, :])

                windows_3d = np.concatenate(window_parts, axis=0) if len(window_parts) > 1 else window_parts[0]
                batch_windows = max(1, min(256, chunk_size // max(1, self.seq_len)))

                for start_w in range(0, windows_3d.shape[0], batch_windows):
                    batch_np = np.ascontiguousarray(windows_3d[start_w : start_w + batch_windows])
                    tensor_x = torch.from_numpy(batch_np)
                    if use_cuda:
                        tensor_x = tensor_x.pin_memory().to(self.device, non_blocking=True)
                    else:
                        tensor_x = tensor_x.to(self.device)

                    tensor_x_norm, mean, std = TensorNormalizer.zscore_norm(tensor_x, seq_dim=1)
                    with autocast(device_type=device_type, dtype=amp_dtype, enabled=use_cuda):
                        x_reconstructed_norm = self.model(tensor_x_norm)

                    x_reconstructed = TensorNormalizer.zscore_denorm(x_reconstructed_norm.float(), mean, std)
                    reconstructed_results.append(x_reconstructed.cpu().float().numpy())

                reconstructed_3d = np.concatenate(reconstructed_results, axis=0)
                reconstructed = reconstructed_3d.reshape(-1, num_feats)[:total_length]
            else:
                batch_size_3d = 128
                for i in range(0, working_seq.shape[0], batch_size_3d):
                    chunk = np.ascontiguousarray(working_seq[i : i + batch_size_3d])
                    tensor_x = torch.from_numpy(chunk)
                    if use_cuda:
                        tensor_x = tensor_x.pin_memory().to(self.device, non_blocking=True)
                    else:
                        tensor_x = tensor_x.to(self.device)

                    tensor_x_norm, mean, std = TensorNormalizer.zscore_norm(tensor_x, seq_dim=1)
                    with autocast(device_type=device_type, dtype=amp_dtype, enabled=use_cuda):
                        x_reconstructed_norm = self.model(tensor_x_norm)

                    x_reconstructed = TensorNormalizer.zscore_denorm(x_reconstructed_norm.float(), mean, std)
                    reconstructed_results.append(x_reconstructed.cpu().float().numpy())

                reconstructed = np.concatenate(reconstructed_results, axis=0)

        # Patch only missing (NaN) positions
        final_output = incomplete_seq.copy()
        final_output[mask] = reconstructed[mask]
        return final_output
