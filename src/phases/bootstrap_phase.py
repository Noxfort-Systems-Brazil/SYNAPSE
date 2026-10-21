# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import glob
from typing import Optional, TYPE_CHECKING
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

# NEW: Import AppState definition
from src.domain.app_state import AppState
from src.utils.logging_setup import get_logger

logger = get_logger("BootstrapPhase")

if TYPE_CHECKING:
    from src.services.offline_service import OfflineService

class BootstrapPhase(QObject):
    """
    Handles Phase 1: Offline Bootstrap.
    
    Location: src/phases/bootstrap_phase.py
    
    Responsibilities:
    - Manages the OfflineService lifecycle.
    - Orchestrates data cleaning, enrichment, and initial model training.
    - INTELLIGENT SKIP: Checks for existing Data Lake, Ontology, and Peak Schedule to bypass processing.
    
    Refactored V3:
    - Added Master Lock validation for peak_schedule.json to prevent premature skipping.
    - Added 0-byte ghost file protection directly in the phase gatekeeper.
    """

    # --- SIGNALS ---
    log_message = pyqtSignal(str)
    bootstrap_finished = pyqtSignal()

    def __init__(self, app_state: AppState):
        """
        Args:
            app_state: The central application state.
        """
        super().__init__()
        self.app_state = app_state # Store the injected state
        
        self.offline_service: Optional['OfflineService'] = None

    def start(self):
        """Starts the offline bootstrap sequence or skips if all data exists."""
        if self.offline_service and self.offline_service.isRunning():
            return
            
        self.log_message.emit(">>> Starting Phase 1: Offline Bootstrap...")
        logger.info("🔒 [Fase 1: Bootstrap Offline] Processamento de dados históricos. Ingestão de sensores ao vivo aguarda a Fase 2.")

        # --- INTELLIGENT SKIP CHECK ---
        # Now strictly requires all three artifacts (Golden, Safetensors, JSON)
        if self._check_existing_datalake():
            self.log_message.emit("Found complete Data Lake (Base + Golden), Ontology, and Peak Schedule.")
            self.log_message.emit(">>> SKIPPING Phase 1: All artifacts are already processed.")
            self.bootstrap_finished.emit()
            return
        
        # Lazy Import to avoid circular dependencies
        from src.services.offline_service import OfflineService
        
        self.offline_service = OfflineService(self.app_state)
        self.offline_service.log_message.connect(self.log_message)
        self.offline_service.bootstrap_finished.connect(self._on_bootstrap_finished)
        self.offline_service.start()

    def stop(self):
        """Stops the bootstrap process if running."""
        if self.offline_service:
            self.offline_service.stop()
            self.offline_service = None

    def _check_existing_datalake(self) -> bool:
        """
        Verifies if the Data Lake structure, ontology, and peak schedule exist AND are valid.
        """
        try:
            from src.storage.path_scaffolder import PathScaffolder
            scaffolder = PathScaffolder()
            base_path = scaffolder.get_datalake_base_path()
            golden_path = scaffolder.get_datalake_golden_path()
            config_path = scaffolder.get_config_path()
            peak_schedule_path = scaffolder.get_config_file("peak_schedule.json")
            
            # 1. Check Directories
            if not os.path.exists(base_path) or not os.path.exists(golden_path):
                return False
                
            # 2. Check for content (.parquet)
            base_files = glob.glob(os.path.join(base_path, "*.parquet"))
            golden_files = glob.glob(os.path.join(golden_path, "*.parquet"))
            
            # 3. Check specific artifacts with Ghost File protection (> 0 bytes)
            json_valid = os.path.exists(peak_schedule_path) and os.path.getsize(peak_schedule_path) > 0
            
            # 4. Check Auditor Calibration Checkpoint
            auditor_path = os.path.join(config_path, "auditor_calibrated.pth")
            auditor_valid = os.path.exists(auditor_path) and os.path.getsize(auditor_path) > 0
            
            # 5. Check Linguist Calibration Checkpoint
            linguist_path = os.path.join(config_path, "linguist_calibrated.json")
            linguist_valid = os.path.exists(linguist_path) and os.path.getsize(linguist_path) > 0
            
            if len(base_files) > 0 and len(golden_files) > 0 and json_valid and auditor_valid and linguist_valid:
                return True
                
            return False
            
        except Exception as e:
            self.log_message.emit(f"⚠️ Error checking Data Lake: {e}")
            return False

    @pyqtSlot()
    def _on_bootstrap_finished(self):
        """Callback when the offline pipeline completes."""
        self.log_message.emit(">>> Bootstrap Complete.")
        self.bootstrap_finished.emit()
        self.offline_service = None
