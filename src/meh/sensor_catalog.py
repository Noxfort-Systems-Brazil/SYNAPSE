# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import List, Optional
import pandas as pd

from src.utils.logging_setup import logger


class SensorCatalog:
    """
    Single Responsibility: Sensor discovery, grouping column resolution,
    and sensor-specific dataset filtering.
    """

    SENSOR_ID_CANDIDATES: List[str] = ['sensor_id', 'device_id', 'camera_id', 'source_id', 'id']

    def __init__(self, candidates: Optional[List[str]] = None):
        self.candidates = candidates or self.SENSOR_ID_CANDIDATES
        self.group_column: Optional[str] = None
        self.sensor_ids: List[str] = []

    def build(self, df: Optional[pd.DataFrame]) -> None:
        """Detects the sensor grouping column and builds a catalog of distinct sensor IDs."""
        if df is None or df.empty:
            self.group_column = None
            self.sensor_ids = []
            return

        self.group_column = next(
            (col for col in self.candidates if col in df.columns),
            None
        )

        if self.group_column:
            self.sensor_ids = list(dict.fromkeys(df[self.group_column].dropna().unique().tolist()))
            logger.info(
                f"[SensorCatalog] 🔍 Sensor column: '{self.group_column}' → "
                f"{len(self.sensor_ids)} distinct sensors cataloged: {self.sensor_ids[:10]}"
            )
        else:
            self.sensor_ids = ['global_sensor']
            logger.info("[SensorCatalog] 🔍 No sensor column detected. Treating as single global sensor.")

    def get_sensor_data(self, df: Optional[pd.DataFrame], sensor_id: str) -> Optional[pd.DataFrame]:
        """Returns only the rows for a specific sensor."""
        if df is None or df.empty:
            return None

        if not self.group_column or sensor_id == 'global_sensor':
            return df

        mask = df[self.group_column] == sensor_id
        return df.loc[mask]
