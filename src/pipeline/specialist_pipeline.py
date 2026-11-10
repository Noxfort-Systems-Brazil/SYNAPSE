# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import List, Any, Optional, Union
from torch.amp import autocast

from src.models.tcn_ae import TCNAE


class SpecialistPipeline:
    """
    Dedicated Neural Pipeline for Temporal Convolutional Autoencoder (TCN-AE) Feature Extraction.
    Encapsulates TCNAE execution, decoding, and embedding generation with device safety and Warmup & Freeze.
    """

    def __init__(
        self,
        model: Optional[nn.ModuleDict] = None,
        input_dim: int = 1,
        output_dim: int = 32,
        num_channels: Optional[List[int]] = None,
        kernel_size: int = 2,
        dropout: float = 0.1,
        device: Optional[torch.device] = None,
        **kwargs: Any
    ):
        self.input_dim = input_dim
        self.output_dim = output_dim
        num_channels = num_channels or [8, 16]

        if model is not None:
            self.model = model
        else:
            tcn = TCNAE(
                num_inputs=input_dim,
                num_channels=num_channels,
                latent_dim=output_dim,
                kernel_size=kernel_size,
                dropout=dropout
            )
            # Retain decoder/reconstruction_head references for backward compatibility
            self.model = nn.ModuleDict({
                "tcn": tcn,
                "decoder": getattr(tcn, "decoder", None),
                "reconstruction_head": getattr(getattr(tcn, "decoder", None), "reconstruct_head", None)
            })

        self.tcn = self.model["tcn"]
        self.decoder = self.model["decoder"] if "decoder" in self.model else None
        self.reconstruction_head = self.model["reconstruction_head"] if "reconstruction_head" in self.model else None
        self._step_state: Optional[dict] = None

        target_device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.to(target_device)

    def _get_current_device(self) -> torch.device:
        try:
            return next(self.tcn.parameters()).device
        except StopIteration:
            return torch.device("cpu")

    def to(self, device: Any) -> 'SpecialistPipeline':
        target_device = torch.device(device) if isinstance(device, str) else device
        self.model.to(target_device)
        self._step_state = None
        return self

    def freeze(self) -> 'SpecialistPipeline':
        """Freezes internal TCNAE weights for zero-cost drift-safe real-time inference."""
        freeze_fn = getattr(self.tcn, "freeze", None)
        if callable(freeze_fn):
            freeze_fn()
        else:
            for param in self.model.parameters():
                param.requires_grad = False
            self.model.eval()
        return self

    def unfreeze(self) -> 'SpecialistPipeline':
        """Unfreezes internal TCNAE weights for on-demand recalibration."""
        unfreeze_fn = getattr(self.tcn, "unfreeze", None)
        if callable(unfreeze_fn):
            unfreeze_fn()
        else:
            for param in self.model.parameters():
                param.requires_grad = True
        return self

    @property
    def is_frozen(self) -> bool:
        tcn_frozen = getattr(self.tcn, "is_frozen", None)
        if tcn_frozen is not None:
            return bool(tcn_frozen() if callable(tcn_frozen) else tcn_frozen)
        return not any(p.requires_grad for p in self.model.parameters())

    def predict(self, input_sequence: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Extracts temporal embeddings using AMP and Safe Device placement.
        Auto-handles dimension permutations and returns the final embedding vector (32-dim).
        """
        self.model.eval()
        device = self._get_current_device()

        with torch.no_grad():
            seq = input_sequence
            if getattr(seq, "ndim", 0) == 2 and seq.shape[0] > seq.shape[1]:
                # Typical memory buffer is [Time, Features], TCN needs [Features, Time]
                seq = seq.T

            if isinstance(seq, np.ndarray):
                tensor_x = torch.FloatTensor(seq).to(device)
            elif isinstance(seq, torch.Tensor):
                tensor_x = seq.to(device)
            else:
                tensor_x = torch.tensor(seq, dtype=torch.float).to(device)

            if tensor_x.dim() == 1:
                tensor_x = tensor_x.unsqueeze(0).unsqueeze(0)
            elif tensor_x.dim() == 2:
                tensor_x = tensor_x.unsqueeze(0)

            device_type = device.type if device.type != 'mps' else 'cpu'

            with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                if isinstance(self.tcn, TCNAE):
                    embedding = self.tcn.encode(tensor_x) # [Batch, LatentDim]
                    output = embedding
                else:
                    tcn_out = self.tcn(tensor_x)
                    if self.decoder is not None:
                        tcn_out_transposed = tcn_out.transpose(1, 2)
                        output = self.decoder(tcn_out_transposed).transpose(1, 2)
                    else:
                        output = tcn_out

            full_seq = output.cpu().float().numpy().squeeze(0)
            if full_seq.ndim == 2:
                return full_seq[:, -1]
            return full_seq

    @property
    def has_step_state(self) -> bool:
        """Returns True if the incremental causal buffer is currently warm for this isolated sensor."""
        return self._step_state is not None

    def reset_step_state(self) -> None:
        """Resets the cached incremental state buffer for this isolated sensor."""
        self._step_state = None

    def _receptive_field(self) -> int:
        k = int(getattr(self.tcn, "kernel_size", 2))
        ch = getattr(self.tcn, "num_channels", [16, 32])
        n_layers = len(ch) if isinstance(ch, (list, tuple)) else 2
        return 1 + 2 * max(0, k - 1) * ((1 << n_layers) - 1)

    def warm_step_state(self, input_sequence: Union[np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Synchronizes the causal state cache from the clean tail of input_sequence (at most R receptive-field steps)
        and returns the resulting latest embedding vector [output_dim].
        """
        self._step_state = None
        if not hasattr(self.tcn, "step"):
            return self.predict(input_sequence)

        arr = input_sequence.detach().cpu().numpy() if isinstance(input_sequence, torch.Tensor) else np.asarray(input_sequence, dtype=np.float32)
        if arr.size == 0:
            return np.zeros(self.output_dim, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        elif arr.ndim == 2 and arr.shape[0] < arr.shape[1] and arr.shape[0] == self.input_dim:
            arr = arr.T

        tail = arr[-self._receptive_field() :]
        last_emb = np.zeros(self.output_dim, dtype=np.float32)
        for idx in range(tail.shape[0]):
            sample = float(tail[idx, 0]) if tail.shape[1] == 1 else tail[idx]
            last_emb = self.predict_step(sample)
        return last_emb

    def predict_step(self, new_sample: Union[float, int, np.ndarray, torch.Tensor]) -> np.ndarray:
        """
        Incremental causal step inference O(1).
        Consumes a single new sample for this isolated sensor, updating the internal state cache.
        Returns:
            embedding: 1D numpy array of shape [output_dim].
        """
        self.model.eval()
        device = self._get_current_device()

        with torch.no_grad():
            if isinstance(new_sample, (float, int)):
                tensor_x = torch.tensor([[[float(new_sample)]]], dtype=torch.float, device=device)
            elif isinstance(new_sample, np.ndarray):
                tensor_x = torch.from_numpy(new_sample).float().to(device)
            elif isinstance(new_sample, torch.Tensor):
                tensor_x = new_sample.float().to(device)
            else:
                tensor_x = torch.tensor(new_sample, dtype=torch.float, device=device)

            if tensor_x.dim() == 1:
                tensor_x = tensor_x.unsqueeze(0).unsqueeze(-1)
            elif tensor_x.dim() == 2:
                tensor_x = tensor_x.unsqueeze(-1)

            device_type = device.type if device.type != 'mps' else 'cpu'
            with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                if hasattr(self.tcn, "step"):
                    latent_t, self._step_state = self.tcn.step(tensor_x, self._step_state)
                else:
                    return self.predict(tensor_x)

            out_np = latent_t.cpu().float().numpy().squeeze()
            if out_np.ndim == 0:
                out_np = np.expand_dims(out_np, 0)
            return out_np


    def compute_loss(self, input_sequence: Union[np.ndarray, torch.Tensor]) -> float:
        """
        Fast-path reconstruction error evaluation via torch.no_grad (<0.05ms).
        Zero gradient and zero backward graph overhead for wire-speed ingestion.
        """
        self.model.eval()
        device = self._get_current_device()

        with torch.no_grad():
            seq = input_sequence
            if getattr(seq, "ndim", 0) == 2 and seq.shape[0] > seq.shape[1]:
                seq = seq.T

            if isinstance(seq, np.ndarray):
                tensor_x = torch.FloatTensor(seq).to(device)
            elif isinstance(seq, torch.Tensor):
                tensor_x = seq.to(device)
            else:
                tensor_x = torch.tensor(seq, dtype=torch.float).to(device)

            if tensor_x.dim() == 1:
                tensor_x = tensor_x.unsqueeze(0).unsqueeze(0)
            elif tensor_x.dim() == 2:
                tensor_x = tensor_x.unsqueeze(0)

            device_type = device.type if device.type != 'mps' else 'cpu'

            # Normalize sequence scale for stable bounded MSE loss
            try:
                max_val = float(torch.max(torch.abs(tensor_x)).item())
                norm_factor = max_val if max_val > 1.0 else 1.0
                norm_x = tensor_x / norm_factor
            except Exception:
                norm_x = tensor_x

            with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                if isinstance(self.tcn, TCNAE):
                    reconstructed, _ = self.tcn(norm_x)
                    return float(F.mse_loss(reconstructed, norm_x).item())
                elif callable(self.tcn):
                    out = self.tcn(norm_x)
                    return float(F.mse_loss(out, norm_x).item())
        return 0.02
