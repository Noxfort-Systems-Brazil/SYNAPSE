# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
from typing import List, Union


class TemporalMemory:
    """
    Manages a sliding window of temporal data (Time Series) via a zero-allocation NumPy ring buffer.
    
    Refactored V4 (Zero-Allocation Ring Buffer):
    - Pre-allocates contiguous float32 memory [max_len, feature_dim] to eliminate GC list pressure.
    - Provides fast conversion methods (Tensor/Numpy).
    - Supports exact O(1) pointer 'rollback' for Physics Fallback recovery even across wrap-arounds.
    """

    def __init__(self, feature_dim: int, max_len: int = 60):
        """
        Args:
            feature_dim: Number of features per time step (e.g., 1 for Flow).
            max_len: Size of the sliding window (Sequence Length).
        """
        self.feature_dim = int(feature_dim)
        self.max_len = int(max_len)
        self._ring = np.zeros((self.max_len, self.feature_dim), dtype=np.float32)
        self._head: int = 0
        self._count: int = 0
        self.device = torch.device("cpu")

    def push(self, data: Union[List[float], np.ndarray, float]) -> None:
        """
        Adds a new time step to the ring buffer in O(1) without heap list allocations.
        Automatically overwrites the oldest entry when full.
        """
        idx = self._head
        if self.feature_dim == 1:
            if isinstance(data, (int, float)):
                self._ring[idx, 0] = float(data)
            elif isinstance(data, list) and len(data) >= 1:
                self._ring[idx, 0] = float(data[0])
            elif isinstance(data, np.ndarray) and data.size >= 1:
                self._ring[idx, 0] = float(data.flat[0])
            else:
                self._ring[idx, 0] = 0.0
        else:
            if isinstance(data, (int, float)):
                self._ring[idx, 0] = float(data)
                self._ring[idx, 1:] = 0.0
            elif isinstance(data, np.ndarray):
                flat = data.reshape(-1)
                n = min(self.feature_dim, flat.size)
                self._ring[idx, :n] = flat[:n]
                if n < self.feature_dim:
                    self._ring[idx, n:] = 0.0
            elif isinstance(data, list):
                n = min(self.feature_dim, len(data))
                for k in range(n):
                    self._ring[idx, k] = float(data[k])
                if n < self.feature_dim:
                    self._ring[idx, n:] = 0.0
            else:
                self._ring[idx, :] = 0.0

        self._head = (idx + 1) % self.max_len
        if self._count < self.max_len:
            self._count += 1

    def is_ready(self) -> bool:
        """Returns True if the buffer is full (Warmed Up)."""
        return self._count >= self.max_len

    def get_numpy(self) -> np.ndarray:
        """
        Returns the ordered sliding window as a contiguous float32 NumPy Array.
        Shape: (Current_Seq_Len, Features) or (max_len, Features) when empty.
        """
        if self._count == 0:
            return np.zeros((self.max_len, self.feature_dim), dtype=np.float32)

        start = (self._head - self._count) % self.max_len
        if start + self._count <= self.max_len:
            return self._ring[start : start + self._count].copy()

        out = np.empty((self._count, self.feature_dim), dtype=np.float32)
        first_part = self.max_len - start
        out[:first_part] = self._ring[start:]
        out[first_part:] = self._ring[: self._count - first_part]
        return out

    def get_tensor(self) -> torch.Tensor:
        """
        Returns the buffer as a PyTorch Tensor via zero-copy NumPy bridge.
        Shape: (Batch=1, Seq_Len, Features)
        """
        if self._count == 0:
            return torch.zeros((1, self.max_len, self.feature_dim), dtype=torch.float32)
        return torch.from_numpy(self.get_numpy()).unsqueeze(0)

    def rollback(self, steps: int) -> None:
        """
        Removes the last N steps in O(1) pointer arithmetic.
        Used when the Physics Engine purges synthetic outage readings upon sensor recovery.
        """
        n = min(max(0, int(steps)), self._count)
        if n > 0:
            self._head = (self._head - n) % self.max_len
            self._count -= n

    def clear(self) -> None:
        """Resets the memory pointers without reallocating the backing array."""
        self._head = 0
        self._count = 0

    def get_state(self) -> List[List[float]]:
        """Returns the ordered buffer contents for checkpointing."""
        if self._count == 0:
            return []
        return self.get_numpy().tolist()

    def set_state(self, state: List[List[float]]) -> None:
        """Restores buffer contents from a checkpoint."""
        self.clear()
        for item in state:
            self.push(item)

    def __len__(self) -> int:
        return self._count
