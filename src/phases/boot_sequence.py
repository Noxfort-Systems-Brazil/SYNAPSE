# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Boot Sequence Phase (SOLID: SRP).

Extracted from LifecycleOrchestrator.boot_system() to respect
Single Responsibility. The orchestrator manages state transitions;
this class handles the actual power-on logic for each subsystem.
"""

import os
from typing import Any, Dict

from src.domain.app_state import AppState
from src.utils.logging_setup import logger


class BootSequence:
    """
    Executes the power-on sequence for all subsystems.
    
    Extracted from LifecycleOrchestrator to follow SRP.
    Each step is isolated and testable independently.
    
    Steps:
        1. Start Fenix Watchdog (reliability monitor)
        2. Inject map data into Cartographer (if available)
        3. Load Cartographer diploma (pre-trained weights)
        4. Initialize InferenceEngine
    """

    @staticmethod
    def execute(app_state: AppState, services: Dict[str, Any]) -> None:
        """
        Runs the full boot sequence.
        
        Args:
            app_state: Central application state.
            services: Dict from ServiceContainer.build().
            
        Raises:
            Exception: Propagated to orchestrator for emergency stop.
        """
        logger.info("[BootSequence] 🔌 Initiating power-on sequence...")

        # Step 1: Start Recovery Watchdog
        fenix = services.get("fenix")
        if fenix:
            fenix.start_watchdog()
            logger.info("[BootSequence] 🛡️ Fenix Watchdog started.")

        # Step 2: Initialize Inference Engine
        engine = services.get("inference_engine")
        if engine:
            engine.initialize_system()
            logger.info("[BootSequence] 🧠 InferenceEngine initialized.")

        logger.info("[BootSequence] ✅ Power-on sequence complete.")

