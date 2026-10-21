# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import gc
import time
from typing import List, Optional
import numpy as np
import pandas as pd

from src.utils.logging_setup import logger


class DatasetPreprocessor:
    """
    Single Responsibility: DataFrame sanitization, memory optimization (downcasting),
    and datetime indexing for historical traffic datasets.
    """

    TIME_COL_CANDIDATES: List[str] = ['timestamp', 'event_timestamp', 'time', 'datetime', 'date']

    def __init__(self, max_rows: int = 500_000):
        self.max_rows = max_rows

    def process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitizes and optimizes a raw DataFrame."""
        if df is None or df.empty:
            return df

        processed_df = df.copy()

        # 1. Cap rows to prevent OOM
        original_len = len(processed_df)
        if original_len > self.max_rows:
            logger.warning(
                f"[DatasetPreprocessor] ⚠️ Dataset has {original_len} rows, "
                f"capping to {self.max_rows} most recent rows to save memory."
            )
            processed_df = processed_df.tail(self.max_rows).reset_index(drop=True)
            gc.collect()
            time.sleep(0.01)

        # 2. Downcast numeric columns to save RAM (float64 -> float32, int64 -> downcast)
        float_cols = processed_df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            processed_df[col] = processed_df[col].astype(np.float32)

        int_cols = processed_df.select_dtypes(include=['int64']).columns
        for col in int_cols:
            processed_df[col] = pd.to_numeric(processed_df[col], downcast='integer')

        # 3. Detect and index timestamp column
        time_col = next((col for col in self.TIME_COL_CANDIDATES if col in processed_df.columns), None)
        if time_col:
            if time_col != 'timestamp':
                processed_df.rename(columns={time_col: 'timestamp'}, inplace=True)

            processed_df['timestamp'] = pd.to_datetime(processed_df['timestamp'])
            processed_df.set_index('timestamp', inplace=True, drop=False)
            processed_df.index.name = 'time_idx'
            processed_df.sort_index(inplace=True)

        return processed_df
