# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.historical_manager import HistoricalManager


class MEHBridge:
    """
    Single Responsibility: Bridge between KSE and MEH (Historical State Module).
    
    Handles:
    - Loading the initial MEH baseline on startup.
    - Periodic refresh of MEH data (time-of-day dependent).
    - Tracking whether MEH provided valid data.
    
    Does NOT handle: transmission, timing, or physics.
    """

    def __init__(self, historical_manager: 'HistoricalManager', refresh_interval: float = 1.0):
        self._historical_manager = historical_manager
        self._refresh_interval = refresh_interval
        self._last_fetch_time = 0.0
        self._is_active = False  # True when MEH is the active data source

    @property
    def is_active(self) -> bool:
        """Returns True if MEH is currently the active data source."""
        return self._is_active
    
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value

    def load_baseline(self) -> Optional[Dict[str, Any]]:
        """
        Loads the initial MEH data as operational baseline.
        
        Returns:
            Dict of edge states if MEH has data, None otherwise.
        """
        try:
            meh_data = self._historical_manager.get_current_state_prediction()
            
            if meh_data:
                self._last_fetch_time = time.time()
                self._is_active = True
                return meh_data
            
            return None
            
        except Exception:
            return None

    def refresh_if_needed(self) -> Optional[Dict[str, Any]]:
        """
        Re-queries MEH for fresh data if enough time has passed.
        MEH data is time-of-day dependent, so values change over time.
        
        Returns:
            Fresh dict of edge states, or None if not time to refresh yet.
        """
        if not self._is_active:
            return None
            
        now = time.time()
        if (now - self._last_fetch_time) < self._refresh_interval:
            return None  # Not time yet
        
        try:
            meh_data = self._historical_manager.get_current_state_prediction()
            
            if meh_data:
                self._last_fetch_time = now
                return meh_data
            
            return None
            
        except Exception:
            return None

    def deactivate(self):
        """Called when real sensor data takes over."""
        self._is_active = False
