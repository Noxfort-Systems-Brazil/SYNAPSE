# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
from typing import Dict, TYPE_CHECKING
from src.utils.logging_setup import logger

# Lazy import for type hinting to avoid circular dependencies
if TYPE_CHECKING:
    from src.meh.data_loader import HistoricalDataLoader

class PlaybackEngine:
    """
    Single Responsibility: Sequential Simulation / Playback.
    Manages the cursor and returns the next frame of data sequentially
    for system testing or as an absolute fallback.
    """
    
    def __init__(self, data_loader: 'HistoricalDataLoader'):
        self.loader = data_loader
        self._playback_cursor = 0

    def get_next_frame(self) -> Dict[str, float]:
        """
        Returns the next row of data sequentially in an infinite loop.
        """
        if not self.loader.is_loaded or self.loader.data is None or self.loader.data.empty:
            return {}

        try:
            row = self.loader.data.iloc[self._playback_cursor].to_dict()
        except IndexError:
            # Safety catch in case data changes underneath
            self._playback_cursor = 0
            row = self.loader.data.iloc[0].to_dict()

        # Advance Cursor
        self._playback_cursor += 1
        
        # Rewind if at the end
        if self._playback_cursor >= len(self.loader.data):
            self._playback_cursor = 0
            logger.debug("[PlaybackEngine] 🔄 Simulation Loop: Rewinding to start.")

        # Filter only numeric values for the flat payload
        clean_row = {k: float(v) for k, v in row.items() if isinstance(v, (int, float, np.number))}
        
        return clean_row

    def reset(self):
        """Resets the simulation cursor to the beginning."""
        self._playback_cursor = 0
