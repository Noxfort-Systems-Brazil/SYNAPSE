# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
AFB Replay Engine — Autonomous Fallback Bridge (Replay of Transmitted Data).

Single Responsibility:
Extracts and replays historical traffic data that Synapse already validated
and transmitted at the same time-of-day.
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from src.afb.replay_data_loader import ReplayDataLoader
from src.physics.constants import DEFAULT_JAM_DENSITY_PER_LANE, density_from_occupancy, SpeedConverter
from src.physics.queue_dynamics import TrafficQueueCalculator

logger = logging.getLogger("Synapse.AFB.ReplayEngine")


class ReplayEngine:
    """
    Historical replay engine for the Autonomous Fallback Bridge.
    Pure CPU / Pandas / Numpy — Zero PyTorch / GPU dependency.
    
    Resolution Hierarchy (MEH-aligned 5 tiers):
    - Level 1: Seconds match (+/- 10s)
    - Level 2: Minutes proximity (+/- 15 min / 900s)
    - Level 3: Same day-of-week & same hour (+/- 1h)
    - Level 4: Same hour across any day (+/- 1h)
    - Level 5: Sensor expected mean / baseline
    """

    def __init__(
        self,
        data_path: Optional[str] = None,
        db_engine: Optional[Any] = None,
        telemetry_reader: Optional[Any] = None,
    ):
        from src.storage.path_scaffolder import PathScaffolder
        self.data_path = data_path or os.path.join(
            PathScaffolder().get_datalake_golden_path(), "golden_v1.parquet"
        )
        self.db_engine = db_engine
        self.telemetry_reader = telemetry_reader
        self.data: Optional[pd.DataFrame] = None
        self.sensor_ids: List[str] = []
        self.is_loaded = False
        self.source_type: str = "none"

        # 1. Try to load from database first (highest priority)
        loaded = self._load_from_db()
        
        # 2. If DB is unavailable or empty, fallback to parquet file
        if not loaded:
            self._load_from_parquet()

    def _load_from_db(self) -> bool:
        """Loads historical transmissions directly from the PostgreSQL database."""
        df, sensor_ids, is_loaded, active_engine = ReplayDataLoader.load_from_db(
            self.db_engine, self.telemetry_reader
        )
        if active_engine is not None and self.db_engine is None:
            self.db_engine = active_engine
        if is_loaded and df is not None:
            self.data = df
            self.sensor_ids = sensor_ids
            self.is_loaded = True
            self.source_type = "database"
            return True
        return False

    def _load_from_parquet(self) -> bool:
        """Loads historical parquet dataset for replay as fallback."""
        df, sensor_ids, is_loaded, resolved_path = ReplayDataLoader.load_from_parquet(self.data_path)
        self.data_path = resolved_path
        if is_loaded and df is not None:
            self.data = df
            self.sensor_ids = sensor_ids
            self.is_loaded = True
            self.source_type = "parquet"
            return True
        self.is_loaded = False
        return False

    def get_replay_frame(self, target_timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        Retrieves historical replay readings matching the target time-of-day
        using the MEH 5-tier hierarchical resolution cascade.
        """
        ts = target_timestamp or time.time()
        target_dt = datetime.fromtimestamp(ts)
        target_seconds = target_dt.hour * 3600 + target_dt.minute * 60 + target_dt.second
        target_dow = target_dt.weekday()
        target_hour = target_dt.hour

        frame: Dict[str, Any] = {
            "_metadata": {
                "strategy": "AFB_DATABASE_REPLAY" if self.source_type == "database" else "AFB_REPLAY",
                "source": self.source_type,
                "timestamp": ts,
                "time_of_day": target_dt.strftime("%H:%M:%S"),
                "day_of_week": target_dow,
                "is_fallback": True,
                "resolution_tier": "tier_5_safe_baseline",
            },
            "readings": {}
        }

        # Safe baseline if no data available
        if not self.is_loaded or self.data is None or self.data.empty:
            speed_ms = SpeedConverter.to_ms(40.0, "km/h")
            base_queue = float(TrafficQueueCalculator.estimate_fallback_queue(density=12.0, speed=speed_ms))
            for sid in self.sensor_ids or ["sensor_fallback"]:
                frame["readings"][sid] = {
                    "speed": 40.0,
                    "density": 12.0,
                    "queue": base_queue,
                    "flow_rate": 200.0,
                    "occupancy": 0.10,
                    "confidence": 0.50,
                    "source": "synthetic_baseline"
                }
            return frame

        dominant_tier = "tier_5_sensor_mean"

        for sid in self.sensor_ids:
            sensor_df = self.data[self.data["sensor_id"] == sid] if "sensor_id" in self.data.columns else self.data
            if sensor_df.empty:
                sensor_df = self.data

            reading, tier = self._resolve_sensor_reading(
                sensor_df, target_dt, target_seconds, target_dow, target_hour
            )
            frame["readings"][sid] = reading
            dominant_tier = tier

        frame["_metadata"]["resolution_tier"] = dominant_tier
        return frame

    def _resolve_sensor_reading(
        self,
        df: pd.DataFrame,
        target_dt: datetime,
        target_seconds: float,
        target_dow: int,
        target_hour: int,
    ) -> Tuple[Dict[str, Any], str]:
        """Applies the 5-Tier Hierarchical Cascade on the given sensor DataFrame."""
        if "timestamp" not in df.columns:
            mean_speed = float(df["speed"].mean()) if "speed" in df.columns else 40.0
            speed_ms = SpeedConverter.to_ms(mean_speed, "km/h") if mean_speed > 35.0 else mean_speed
            calc_queue = float(TrafficQueueCalculator.estimate_fallback_queue(density=10.0, speed=speed_ms))
            return {
                "speed": mean_speed,
                "density": 10.0,
                "queue": calc_queue,
                "flow_rate": 200.0,
                "occupancy": 0.10,
                "confidence": 0.50,
                "source": "synapse_historical_mean"
            }, "tier_5_sensor_mean"

        ts_col = df["timestamp"]
        row_seconds = ts_col.dt.hour * 3600 + ts_col.dt.minute * 60 + ts_col.dt.second
        sec_diff = (row_seconds - target_seconds).abs()

        matched_row: Optional[pd.Series] = None
        tier = "tier_5_sensor_mean"
        confidence = 0.50

        # --- LEVEL 1: Exact Seconds Proximity (<= 10s) ---
        min_sec_diff = sec_diff.min()
        if min_sec_diff <= 10.0:
            best_idx = sec_diff.idxmin()
            matched_row = df.loc[best_idx]
            tier = "tier_1_seconds"
            confidence = 0.95

        # --- LEVEL 2: Minutes Proximity (<= 15 min / 900s) ---
        elif min_sec_diff <= 900.0:
            best_idx = sec_diff.idxmin()
            matched_row = df.loc[best_idx]
            tier = "tier_2_minutes"
            confidence = 0.85

        # --- LEVEL 3: Same Day-of-Week & Same Hour (+/- 1h) ---
        else:
            dow_mask = (ts_col.dt.dayofweek == target_dow) & ((ts_col.dt.hour - target_hour).abs() <= 1)
            dow_df = df.loc[dow_mask]
            if not dow_df.empty:
                dow_sec_diff = sec_diff.loc[dow_df.index]
                best_idx = dow_sec_diff.idxmin()
                matched_row = df.loc[best_idx]
                tier = "tier_3_weekday_hour"
                confidence = 0.75

            # --- LEVEL 4: Same Hour Across Any Day (+/- 1h) ---
            else:
                hour_mask = (ts_col.dt.hour - target_hour).abs() <= 1
                hour_df = df.loc[hour_mask]
                if not hour_df.empty:
                    hour_sec_diff = sec_diff.loc[hour_df.index]
                    best_idx = hour_sec_diff.idxmin()
                    matched_row = df.loc[best_idx]
                    tier = "tier_4_global_hour"
                    confidence = 0.65

        # Extract values from matched row or fall back to Level 5 mean
        if matched_row is not None:
            speed = float(matched_row["speed"]) if "speed" in matched_row and pd.notna(matched_row["speed"]) else 40.0
            flow_rate = float(matched_row["flow_rate"]) if "flow_rate" in matched_row and pd.notna(matched_row["flow_rate"]) else 200.0
            occupancy = float(matched_row["occupancy"]) if "occupancy" in matched_row and pd.notna(matched_row["occupancy"]) else 0.10
            density = float(matched_row["density"]) if "density" in matched_row and pd.notna(matched_row["density"]) else density_from_occupancy(occupancy, DEFAULT_JAM_DENSITY_PER_LANE)
            queue = float(matched_row["queue"]) if "queue" in matched_row and pd.notna(matched_row["queue"]) else 0.0
            if queue <= 0.0:
                speed_ms = SpeedConverter.to_ms(speed, "km/h") if speed > 35.0 else speed
                queue = float(TrafficQueueCalculator.estimate_fallback_queue(density=density, speed=speed_ms))
        else:
            tier = "tier_5_sensor_mean"
            confidence = 0.50
            speed = float(df["speed"].mean()) if "speed" in df.columns and not df["speed"].dropna().empty else 40.0
            flow_rate = float(df["flow_rate"].mean()) if "flow_rate" in df.columns and not df["flow_rate"].dropna().empty else 200.0
            occupancy = float(df["occupancy"].mean()) if "occupancy" in df.columns and not df["occupancy"].dropna().empty else 0.10
            density = density_from_occupancy(occupancy, DEFAULT_JAM_DENSITY_PER_LANE)
            speed_ms = SpeedConverter.to_ms(speed, "km/h") if speed > 35.0 else speed
            queue = float(TrafficQueueCalculator.estimate_fallback_queue(density=density, speed=speed_ms))

        reading = {
            "speed": speed,
            "density": density,
            "queue": queue,
            "flow_rate": flow_rate,
            "occupancy": occupancy,
            "confidence": confidence,
            "source": f"synapse_historical_{self.source_type}"
        }
        return reading, tier
