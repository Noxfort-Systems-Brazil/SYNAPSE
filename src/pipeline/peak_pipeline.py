# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
import gc
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch.amp import autocast
from sklearn.mixture import GaussianMixture
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ColumnDiscovery:
    """
    Discovers volume/flow and speed/velocity columns from Golden Parquet or historical datasets.
    Prioritizes canonical Golden Parquet columns ('flow_val', 'speed_val') with fast keyword fallback,
    completely eliminating the heavy ModernBERT transformer dependency.
    """

    VOLUME_CANDIDATES = [
        "flow_val", "flow", "currentflow", "current_flow", "fluxo",
        "volume", "intensity_val", "intensity", "count", "vehicle_count",
        "veic", "q", "vol"
    ]
    SPEED_CANDIDATES = [
        "speed_val", "speed", "currentspeed", "current_speed", "velocidade",
        "vel", "speed_kmh", "kmh", "v"
    ]

    def discover(self, columns: list) -> Tuple[str, str]:
        """
        Discovers which columns map to volume/flow and speed/velocity.
        
        Returns:
            Tuple of (volume_column, speed_column).
        """
        col_lower = {str(c).lower(): c for c in columns}

        # 1. Exact canonical Golden Parquet check
        vol_col = None
        for cand in self.VOLUME_CANDIDATES:
            if cand in col_lower:
                vol_col = col_lower[cand]
                break

        spd_col = None
        for cand in self.SPEED_CANDIDATES:
            if cand in col_lower:
                spd_col = col_lower[cand]
                break

        # 2. Fallbacks if custom columns are provided
        if not vol_col and columns:
            vol_col = columns[0]
        if not spd_col and len(columns) > 1:
            remaining = [c for c in columns if c != vol_col]
            spd_col = remaining[0] if remaining else columns[0]
        elif not spd_col and columns:
            spd_col = columns[0]

        return vol_col, spd_col


class PeakPipeline:
    """
    Single Responsibility: Peak classification pipeline.
    
    Orchestrates the full ADAGIO pipeline:
    1. Neural feature extraction (iTransformer + TimesNet) in chunks
    2. Canonical week aggregation (168 hourly blocks)
    3. GMM probabilistic classification
    4. JSON schedule export
    """

    DAY_MAP = {
        0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday",
        4: "Friday", 5: "Saturday", 6: "Sunday"
    }

    def __init__(self, itransformer, timesnet, device: torch.device, chunk_size: int = 2048):
        self.itransformer = itransformer
        self.timesnet = timesnet
        self.device = device
        self.chunk_size = chunk_size
        self.gmm = GaussianMixture(n_components=2, covariance_type='full', random_state=42)

    def run(self, df: pd.DataFrame, vol_col: str, spd_col: str, output_path: str) -> dict:
        """
        Executes the full peak classification pipeline.
        
        Returns:
            Dict with the 168-block schedule.
        """
        # 1. Prepare tensors
        volume_tensor = torch.tensor(df[vol_col].values, dtype=torch.float32).unsqueeze(0)
        speed_tensor = torch.tensor(df[spd_col].values, dtype=torch.float32).unsqueeze(0)

        # 2. Neural feature extraction
        logger.info("Extracting neural features via iTransformer + TimesNet...")
        neural_scores = self._extract_features(volume_tensor, speed_tensor)

        # 3. Canonical week
        logger.info("Building canonical week (168 blocks)...")
        canonical_week = self._build_canonical_week(df, neural_scores, vol_col=vol_col)

        # 4. GMM classification
        logger.info("Applying GMM classification...")
        scores_matrix = canonical_week['neural_score'].values.reshape(-1, 1)
        self.gmm.fit(scores_matrix)
        cluster_labels = self.gmm.predict(scores_matrix)

        # Anchor cluster polarity to actual physical traffic volume so negative random
        # projections never invert daytime peak hours with midnight low-flow hours.
        if 'mean_volume' in canonical_week.columns and len(np.unique(cluster_labels)) > 1:
            vol_by_cluster = [
                float(canonical_week.loc[cluster_labels == c, 'mean_volume'].mean())
                for c in range(self.gmm.n_components)
            ]
            if not np.allclose(vol_by_cluster[0], vol_by_cluster[1]):
                peak_cluster_index = int(np.argmax(vol_by_cluster))
            else:
                cluster_means = self.gmm.means_.flatten()
                peak_cluster_index = int(np.argmax(cluster_means))
        else:
            cluster_means = self.gmm.means_.flatten()
            peak_cluster_index = int(np.argmax(cluster_means))
        is_peak = (cluster_labels == peak_cluster_index)

        # 5. Export
        schedule = self._generate_schedule(canonical_week, is_peak)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, indent=4)

        logger.info(f"Peak schedule saved to: {output_path}")
        return schedule

    def _extract_features(self, volume: torch.Tensor, speed: torch.Tensor) -> np.ndarray:
        """Chunked neural feature extraction to prevent VRAM overflow (AMP accelerated)."""
        all_features = []
        total_len = volume.shape[1]
        device_type = self.device.type if self.device.type != 'mps' else 'cpu'

        for i in range(0, total_len, self.chunk_size):
            vol_chunk = volume[:, i:i + self.chunk_size]
            spd_chunk = speed[:, i:i + self.chunk_size]
            current_len = vol_chunk.shape[1]

            if current_len < self.chunk_size:
                pad_len = self.chunk_size - current_len
                vol_chunk = F.pad(vol_chunk, (0, pad_len), mode='constant', value=0.0)
                spd_chunk = F.pad(spd_chunk, (0, pad_len), mode='constant', value=0.0)

            with torch.no_grad():
                multivariate = torch.stack((vol_chunk, spd_chunk), dim=-1).to(self.device)
                with autocast(device_type=device_type, enabled=(self.device.type == 'cuda')):
                    stress = self.itransformer(multivariate)
                    features = self.timesnet(stress)
                chunk_result = features.mean(dim=-1).cpu().float().numpy().flatten()

                if current_len < self.chunk_size:
                    chunk_result = chunk_result[:current_len]
                all_features.append(chunk_result)

            del multivariate, stress, features
            torch.cuda.empty_cache()
            gc.collect()

        return np.concatenate(all_features)

    @staticmethod
    def _build_canonical_week(df: pd.DataFrame, neural_scores: np.ndarray, vol_col: Optional[str] = None) -> pd.DataFrame:
        """Groups neural scores and physical volume by day-of-week and hour."""
        df = df.copy()
        df['neural_score'] = neural_scores

        time_col = 'timestamp' if 'timestamp' in df.columns else 'event_timestamp'
        df[time_col] = pd.to_datetime(df[time_col])
        df['day_of_week'] = df[time_col].dt.dayofweek
        df['hour'] = df[time_col].dt.hour

        if vol_col and vol_col in df.columns:
            df['mean_volume'] = pd.to_numeric(df[vol_col], errors='coerce').fillna(0.0)
            return df.groupby(['day_of_week', 'hour'])[['neural_score', 'mean_volume']].mean().reset_index()

        return df.groupby(['day_of_week', 'hour'])['neural_score'].mean().reset_index()

    @classmethod
    def _generate_schedule(cls, canonical_week: pd.DataFrame, predictions: np.ndarray) -> dict:
        """Formats the 168 blocks into JSON structure."""
        canonical_week['is_peak'] = predictions
        schedule = {day: {} for day in cls.DAY_MAP.values()}

        for day_name in cls.DAY_MAP.values():
            for h in range(24):
                schedule[day_name][f"{h:02d}:00"] = False

        for _, row in canonical_week.iterrows():
            day_name = cls.DAY_MAP[int(row['day_of_week'])]
            schedule[day_name][f"{int(row['hour']):02d}:00"] = bool(row['is_peak'])

        return schedule
