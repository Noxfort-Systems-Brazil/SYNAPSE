# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
from typing import Any, Optional, List, Tuple
import pandas as pd

logger = logging.getLogger("Synapse.AFB.ReplayDataLoader")


class ReplayDataLoader:
    """Handles loading and normalizing historical telemetry for replay (DB & Parquet)."""

    @staticmethod
    def load_from_db(
        db_engine: Optional[Any] = None,
        telemetry_reader: Optional[Any] = None,
    ) -> Tuple[Optional[pd.DataFrame], List[str], bool, Optional[Any]]:
        """
        Loads historical transmissions directly from PostgreSQL telemetry.
        Returns: (df, sensor_ids, is_loaded, db_engine)
        """
        try:
            reader = telemetry_reader
            active_engine = db_engine
            if reader is None:
                if active_engine is None:
                    try:
                        from src.database.db_engine import DatabaseEngine
                        active_engine = DatabaseEngine()
                    except Exception:
                        active_engine = None

                if active_engine is not None:
                    from src.repositories.sensor_telemetry_reader import SensorTelemetryReader
                    reader = SensorTelemetryReader(active_engine)

            if reader is not None:
                samples = reader.query_telemetry_history(limit_seconds=None)
                if samples:
                    df = pd.DataFrame(samples)
                    if not df.empty and "collected_at" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["collected_at"])
                        
                        sensor_col = "sensor_str_id" if "sensor_str_id" in df.columns else "sensor_int_id"
                        if sensor_col in df.columns:
                            df["sensor_id"] = df[sensor_col].astype(str)
                            sensor_ids = list(dict.fromkeys(df["sensor_id"].dropna().unique().tolist()))
                        else:
                            df["sensor_id"] = "global_sensor"
                            sensor_ids = ["global_sensor"]

                        logger.info(f"[ReplayDataLoader] Loaded {len(df)} records for {len(sensor_ids)} sensors from database.")
                        return df, sensor_ids, True, active_engine
        except Exception as e:
            logger.debug(f"[ReplayDataLoader] Could not load telemetry from DB: {e}")

        return None, [], False, active_engine

    @staticmethod
    def load_from_parquet(data_path: str) -> Tuple[Optional[pd.DataFrame], List[str], bool, str]:
        """
        Loads historical parquet dataset for replay fallback.
        Returns: (df, sensor_ids, is_loaded, resolved_data_path)
        """
        resolved_path = data_path
        if not os.path.exists(resolved_path):
            alt_path = os.path.join(os.getcwd(), "data", "datalake", "golden", "golden_v1.parquet")
            if os.path.exists(alt_path):
                resolved_path = alt_path
            else:
                return None, [], False, resolved_path

        try:
            df = pd.read_parquet(resolved_path)
            
            # Detect sensor column
            candidates = ['sensor_id', 'device_id', 'camera_id', 'source_id', 'id']
            group_col = next((c for c in candidates if c in df.columns), None)
            
            if group_col:
                df["sensor_id"] = df[group_col].astype(str)
                sensor_ids = list(dict.fromkeys(df["sensor_id"].dropna().unique().tolist()))
            else:
                df["sensor_id"] = 'global_sensor'
                sensor_ids = ['global_sensor']

            # Auto-detect timestamp column
            time_cols = ['timestamp', 'event_timestamp', 'time', 'datetime', 'date']
            time_col = next((c for c in time_cols if c in df.columns), None)
            if time_col:
                if time_col != 'timestamp':
                    df.rename(columns={time_col: 'timestamp'}, inplace=True)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            logger.info(f"[ReplayDataLoader] Loaded {len(df)} records from parquet: {resolved_path}")
            return df, sensor_ids, True, resolved_path
        except Exception as e:
            logger.warning(f"[ReplayDataLoader] Failed to load parquet dataset: {e}")
            return None, [], False, resolved_path
