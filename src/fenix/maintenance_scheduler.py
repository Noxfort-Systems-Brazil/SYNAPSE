# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
from src.utils.logging_setup import logger


class MaintenanceScheduler:
    """
    Manages autonomous opportunity window scanning based on a weekly schedule.
    Slot states: 0 = VALLEY (maintenance window), 1 = NORMAL, 2 = PEAK.
    """

    def __init__(self, schedule_path: Optional[Path] = None):
        self.schedule_path = schedule_path or Path("Synapse/data/maintenance_schedule.json")
        self.schedule_map: Dict[str, int] = {}

    def load_schedule(self) -> Dict[str, int]:
        """Loads schedule JSON mapping from disk."""
        if self.schedule_path.exists():
            try:
                with open(self.schedule_path, 'r', encoding='utf-8') as f:
                    self.schedule_map = json.load(f)
                logger.info(f"[MaintenanceScheduler] 📅 Maintenance Schedule Loaded ({len(self.schedule_map)} slots).")
            except Exception as e:
                logger.error(f"[MaintenanceScheduler] Failed to load schedule JSON: {e}")
                self.schedule_map = {}
        else:
            self.schedule_map = {}
        return self.schedule_map

    def is_opportunity_slot(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        Checks if given or current datetime falls into a Valley slot (0).
        
        Returns:
            Tuple[bool, str]: (is_valley, slot_key formatted as 'weekday_hour')
        """
        now = dt or datetime.now()
        key = f"{now.weekday()}_{now.hour}"
        state = self.schedule_map.get(key, 1)  # Default to 1 (NORMAL)
        return (state == 0, key)

    def clear(self):
        """Clears loaded schedule."""
        self.schedule_map = {}
