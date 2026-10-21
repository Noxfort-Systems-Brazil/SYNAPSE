# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from enum import Enum, auto
from typing import Callable, List

# --- Internal Signal Implementation (Observer Pattern) ---
class Signal:
    """
    Implements a lightweight Signal-Slot mechanism to decouple
    the controller from the UI view, replacing PyQt signals.
    Shared across all controllers to maintain consistent communication.
    """
    def __init__(self, name: str = "Signal"):
        self.name = name
        self._observers: List[Callable] = []

    def connect(self, observer: Callable):
        if observer not in self._observers:
            self._observers.append(observer)

    def emit(self, *args, **kwargs):
        for observer in self._observers:
            try:
                emit_fn = getattr(observer, "emit", None)
                if callable(emit_fn):
                    emit_fn(*args, **kwargs)
                else:
                    observer(*args, **kwargs)
            except Exception as e:
                obs_name = getattr(observer, '__name__', type(observer).__name__)
                logging.error(f"[Signal:{self.name}] Error in observer '{obs_name}': {e}")

# --- System States ---
class SystemState(Enum):
    """
    Defines the global lifecycle states of the SYNAPSE system.
    Used by the main orchestrator and sub-controllers to synchronize behavior.
    """
    OFFLINE = auto()            # System Starting / Initializing
    READY = auto()              # Idle / Waiting for Buttons
    PHASE_0_OPTIMIZING = auto() # Running Optuna (or skipping)
    PHASE_1_OFFLINE = auto()    # Running Data Pipeline (or skipping)
    PHASE_2_RUNNING = auto()    # Running Online Inference
    ERROR = auto()              # Critical failure state
    SHUTTING_DOWN = auto()      # Graceful shutdown process
