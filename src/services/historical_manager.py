# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, TYPE_CHECKING
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.logging_setup import logger
from src.utils.singleton_qobject import SingletonQObject
from src.meh.data_loader import HistoricalDataLoader
from src.meh.fallback_engine import FallbackEngine
from src.meh.playback_engine import PlaybackEngine
from src.meh.edge_payload_formatter import EdgePayloadFormatter

if TYPE_CHECKING:
    from src.domain.app_state import AppState


class HistoricalManager(QObject, metaclass=SingletonQObject):
    """
    Facade/Orchestrator for the Historical and MEH (Historical State Module) subsystems.
    Singleton Pattern: Ensures a single centralized instance across the entire application lifecycle.
    """

    data_loaded = pyqtSignal(bool)

    def __init__(self, app_state: Optional['AppState'] = None, lazy_load: bool = False, async_load: bool = False):
        super().__init__()
        self._initialized = True
        self.app_state = app_state
        self._is_loading = False
        self._load_lock = threading.Lock()

        # Instantiate specialized MEH engines
        self.loader = HistoricalDataLoader()
        self.fallback_engine = FallbackEngine(self.loader)
        self.playback_engine = PlaybackEngine(self.loader)

        if async_load:
            self.load_data_async()
        elif not lazy_load:
            self.load_data()

    def load_data(self, force_recompute: bool = False) -> bool:
        """Orchestrates loading data and building MEH profiles."""
        with self._load_lock:
            self._is_loading = True
            try:
                success = self.loader.load()
                if success:
                    self.fallback_engine.build_profiles(force_recompute=force_recompute)
                    self.playback_engine.reset()
                    self.data_loaded.emit(True)
                    return True
                else:
                    self.data_loaded.emit(False)
                    return False
            finally:
                self._is_loading = False

    def load_data_async(self, callback: Optional[Callable[[bool], None]] = None) -> None:
        """Asynchronously loads historical data on a background worker thread."""
        def _target():
            res = self.load_data()
            if callback:
                callback(res)

        thread = threading.Thread(target=_target, daemon=True, name="HistoricalManagerWarmupThread")
        thread.start()

    def get_fallback_edge_payload(
        self,
        target_time: datetime,
        app_state: Optional['AppState'] = None
    ) -> Dict[str, Dict[str, float]]:
        """Synthesizes structured edge statistics using Level 3/4 MEH profile."""
        flat_data = self.get_meh_state(target_time)
        effective_app_state = app_state or self.app_state
        return EdgePayloadFormatter.format_edge_payload(
            flat_data=flat_data,
            app_state=effective_app_state,
            sensor_profiles=self.fallback_engine.sensor_profiles
        )

    def get_current_state_prediction(self) -> Dict[str, dict]:
        """Backward-compatible alias for KSEManager and tests."""
        return self.get_fallback_edge_payload(datetime.now(), self.app_state)

    def get_exact_reading(self, sensor_id: str, target_timestamp: float, tolerance: float = 0.25) -> Optional[float]:
        return self.loader.get_exact_reading(sensor_id, target_timestamp, tolerance)

    def get_hierarchical_reading(
        self,
        sensor_id: str,
        target_timestamp: float,
        level_tolerances: Optional[Dict[str, float]] = None
    ) -> Optional[float]:
        return self.loader.get_hierarchical_reading(sensor_id, target_timestamp, level_tolerances)

    def get_meh_state(self, target_time: datetime) -> Dict[str, Any]:
        state = self.fallback_engine.get_fallback_state(target_time)
        if not state:
            logger.warning("[HistoricalManager] MEH Fallback failed, degrading to Playback Simulation.")
            return self.get_next_playback_frame()
        return state

    def get_next_playback_frame(self) -> Dict[str, float]:
        return self.playback_engine.get_next_frame()

    def reset_playback(self):
        self.playback_engine.reset()

    def get_expected_value(self, metric_name: str) -> float:
        return self.loader.get_expected_value(metric_name)

    def get_context_window(self, window_size: int = 60) -> np.ndarray:
        return self.loader.get_context_window(window_size)

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        return self.loader.stats_cache

    @property
    def columns(self) -> List[str]:
        return self.loader.columns

    @property
    def is_ready(self) -> bool:
        return self.loader.is_loaded and self.fallback_engine.is_ready
