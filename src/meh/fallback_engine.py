# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import gc
import time
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING
from src.utils.logging_setup import logger

# Lazy import for type hinting to avoid circular dependencies
if TYPE_CHECKING:
    from src.meh.data_loader import HistoricalDataLoader

class FallbackEngine:
    """
    Single Responsibility: Fallback Logic & Digital Twin Simulation.
    Calculates dynamic sensor frequencies, builds historical profiles,
    and resolves the Level 1/Level 2 degradation cascade for MEH state.
    """
    
    # Maximum time bins per sensor to cap memory
    MAX_BINS_PER_SENSOR = 10_000
    
    def __init__(self, data_loader: 'HistoricalDataLoader'):
        self.loader = data_loader
        # Lightweight dict profiles: {sensor_id: {(day, bin): {col: value}}}
        self.sensor_profiles: Dict[str, Dict[tuple, Dict[str, float]]] = {}
        self.sensor_frequencies: Dict[str, float] = {}
        self.is_ready = False

    def build_profiles(self, force_recompute: bool = False):
        """
        Analyzes historical data to find sensor frequencies and build aggregated time bins.
        Must be called after the DataLoader has successfully loaded the data.
        
        Memory-Optimized V3 + Disk Cache:
        - Checks for existing compiled binary cache (profiles_cache_v1.pkl).
        - If cache is valid and up-to-date, loads instantly (~2ms) with zero CPU overhead.
        - Otherwise, calculates profiles, converts to lightweight dict-of-dicts, and persists cache.
        """
        cache_file = None
        gold_path = getattr(self.loader, "gold_path", None)
        if gold_path:
            cache_file = os.path.join(os.path.dirname(gold_path), "profiles_cache_v1.pkl")

        if not force_recompute and cache_file and os.path.exists(cache_file):
            try:
                gold_mtime = os.path.getmtime(gold_path) if os.path.exists(gold_path) else 0
                cache_mtime = os.path.getmtime(cache_file)
                if cache_mtime >= gold_mtime:
                    with open(cache_file, "rb") as f:
                        cached_data = pickle.load(f)
                    if (
                        isinstance(cached_data, dict)
                        and "sensor_profiles" in cached_data
                        and "sensor_frequencies" in cached_data
                    ):
                        self.sensor_profiles = cached_data["sensor_profiles"]
                        self.sensor_frequencies = cached_data["sensor_frequencies"]
                        self.is_ready = True
                        logger.info(
                            f"[FallbackEngine] ⚡ Loaded cached historical profiles ({len(self.sensor_profiles)} sensors) from {cache_file}."
                        )
                        return
            except Exception as e:
                logger.warning(f"[FallbackEngine] Failed to load cache from {cache_file}, recomputing: {e}")

        if not self.loader.is_loaded or self.loader.data is None or self.loader.data.empty:
            logger.warning("[FallbackEngine] Cannot build profiles: DataLoader is empty or not loaded.")
            self.is_ready = False
            return

        df = self.loader.data  # Reference, NOT copy
        
        # Use the DataLoader's detected group column
        group_col = self.loader.group_column
        if not group_col:
            # Fallback: add synthetic column
            df['sensor_id'] = 'global_sensor'
            group_col = 'sensor_id'

        excluded_helper_cols = {'_day_of_week', '_seconds_since_midnight', 'day_of_week', 'time_bin'}
        numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns.tolist()
                        if c not in excluded_helper_cols]

        # Pre-compute helper columns in-place (once for all sensors)
        _added_cols = []
        if '_seconds_since_midnight' not in df.columns:
            df['_seconds_since_midnight'] = (
                df['timestamp'].dt.hour * 3600 +
                df['timestamp'].dt.minute * 60 +
                df['timestamp'].dt.second
            )
            _added_cols.append('_seconds_since_midnight')
        if '_day_of_week' not in df.columns:
            df['_day_of_week'] = df['timestamp'].dt.dayofweek
            _added_cols.append('_day_of_week')

        logger.info(f"[FallbackEngine] Building profiles for {len(self.loader.sensor_ids)} sensors ({len(df)} records)...")

        grouped = df.groupby(group_col)
        
        for sensor_id, group_df in grouped:
            # Calculate dynamic frequency (Digital Twin heartbeat)
            if len(group_df) > 1:
                deltas = group_df['timestamp'].diff().dt.total_seconds().dropna()
                freq_sec = float(deltas.median())
                if freq_sec <= 0 or pd.isna(freq_sec): 
                    freq_sec = 1.0
            else:
                freq_sec = 1.0
                
            self.sensor_frequencies[sensor_id] = freq_sec
            
            # Compute time bins using the pre-calculated seconds column
            time_bins = (group_df['_seconds_since_midnight'] // freq_sec) * freq_sec
            
            # Build aggregated profile — numeric columns only (no text copy overhead)
            agg_dict = {col: 'mean' for col in numeric_cols 
                        if col in group_df.columns and col not in excluded_helper_cols}

            if not agg_dict:
                continue

            # Minimal temporary DataFrame (only needed columns)
            cols_needed = list(agg_dict.keys()) + ['_day_of_week']
            cols_needed = [c for c in cols_needed if c in group_df.columns]
            temp = group_df[cols_needed].copy()
            temp['time_bin'] = time_bins.values
            temp['day_of_week'] = temp['_day_of_week']
            if '_day_of_week' in temp.columns:
                temp.drop(columns=['_day_of_week'], inplace=True)

            profile_df = temp.groupby(['day_of_week', 'time_bin']).agg(agg_dict).reset_index()
            
            # Cap bins to prevent memory explosion
            if len(profile_df) > self.MAX_BINS_PER_SENSOR:
                profile_df = profile_df.sample(n=self.MAX_BINS_PER_SENSOR, random_state=42)
            
            # Convert to lightweight dict-of-dicts: {(day, bin): {col: val}}
            profile_dict = {}
            value_cols = [c for c in profile_df.columns if c not in ['day_of_week', 'time_bin']]
            for _, row in profile_df.iterrows():
                key = (int(row['day_of_week']), float(row['time_bin']))
                profile_dict[key] = {col: float(row[col]) for col in value_cols if pd.notna(row[col])}
            
            self.sensor_profiles[sensor_id] = profile_dict
            
            # Free intermediate memory structures
            del temp, profile_df
            
            # Explicitly yield the Global Interpreter Lock (GIL) to allow 
            # the HFTBootstrapper async generator to dispatch frames.
            time.sleep(0.005)
            
            logger.debug(f"[FallbackEngine] Sensor '{sensor_id}' mapped: Freq={freq_sec:.2f}s, Bins={len(profile_dict)}.")

        # Cleanup: remove helper columns from the source DataFrame
        for col in _added_cols:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

        gc.collect()
        self.is_ready = True
        logger.info(f"[FallbackEngine] Historical profiles built successfully. {len(self.sensor_profiles)} sensors mapped. Ready for fallback.")

        # Save to disk cache atomically
        if cache_file and self.sensor_profiles:
            try:
                tmp_cache = f"{cache_file}.tmp_{os.getpid()}"
                with open(tmp_cache, "wb") as f:
                    pickle.dump({
                        "sensor_profiles": self.sensor_profiles,
                        "sensor_frequencies": self.sensor_frequencies,
                        "cached_at": time.time()
                    }, f, protocol=pickle.HIGHEST_PROTOCOL)
                os.replace(tmp_cache, cache_file)
                logger.info(f"[FallbackEngine] 💾 Saved {len(self.sensor_profiles)} sensor profiles to disk cache: {cache_file}")
            except Exception as e:
                logger.warning(f"[FallbackEngine] Could not persist profiles to disk cache: {e}")

    def get_fallback_state(self, target_time: datetime) -> Dict[str, Any]:
        """
        Resolves the temporal lookup matching the Level 1 and Level 2 cascade logic.
        Uses lightweight dict-based profiles (V3).
        Returns a flat dictionary mapping expected values for the target time.
        """
        if not self.is_ready:
            return {}

        target_day = target_time.weekday()
        seconds_since_midnight = target_time.hour * 3600 + target_time.minute * 60 + target_time.second
        
        flat_payload = {}

        for sensor_id, profile_dict in self.sensor_profiles.items():
            freq_sec = self.sensor_frequencies.get(sensor_id, 1.0)
            target_bin = (seconds_since_midnight // freq_sec) * freq_sec
            
            # Attempt Level 1: Exact Match (Same Day + Same Bin)
            key_exact = (target_day, target_bin)
            match_data = profile_dict.get(key_exact)
            
            if match_data is None:
                # Attempt Level 2: Broad Match (Average across all days for same bin)
                same_bin_entries = [
                    vals for (day, tbin), vals in profile_dict.items()
                    if tbin == target_bin
                ]
                if same_bin_entries:
                    # Average across matched entries
                    match_data = {}
                    all_keys = same_bin_entries[0].keys()
                    for k in all_keys:
                        values = [e[k] for e in same_bin_entries if k in e]
                        match_data[k] = sum(values) / len(values) if values else 0.0
                else:
                    # Missing bin entirely, skip this sensor for this tick
                    continue
            
            flat_payload.update(match_data)

        return flat_payload
