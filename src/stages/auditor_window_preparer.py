# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional
import numpy as np
import pandas as pd


class AuditorWindowPreparer:
    """Extracts and cleans numerical sliding windows from historical Parquet dataset."""

    @staticmethod
    def prepare_windows(golden_path: str, window_size: int = 60) -> Optional[np.ndarray]:
        """
        Loads the Golden Dataset and creates sliding windows for training.
        
        Returns:
            np.ndarray of shape [N, window_size] — flattened feature windows or None if invalid.
        """
        try:
            df = pd.read_parquet(golden_path)
        except Exception:
            return None

        excluded_spatial = {"lat", "lon", "latitude", "longitude"}
        numeric_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if str(c).lower() not in excluded_spatial
        ]
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols:
            return None

        # Clean NaN/Inf in the dataframe
        df_clean = df[numeric_cols].ffill().bfill().fillna(0.0)
        data = df_clean.values.astype(np.float32)
        data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

        # If total features per row >= window_size, use rows directly
        if data.shape[1] >= window_size:
            return data[:, :window_size]

        # Otherwise, create sliding windows from each column independently
        windows = []
        for col_idx in range(data.shape[1]):
            series = data[:, col_idx]
            n_windows = len(series) - window_size + 1
            if n_windows <= 0:
                continue
            for start in range(0, n_windows, window_size // 2):  # 50% overlap
                end = start + window_size
                if end > len(series):
                    break
                windows.append(series[start:end])

        if not windows:
            return None

        return np.array(windows, dtype=np.float32)
