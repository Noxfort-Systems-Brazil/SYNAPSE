# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import traceback
from PyQt6.QtCore import QThread, pyqtSignal

# Import Domain
from src.domain.app_state import AppState

# Import Pipeline Stages
from src.stages.sanitization_stage import SanitizationStage
from src.stages.classification_stage import ClassificationStage
from src.stages.linguist_calibration_stage import LinguistCalibrationStage
from src.stages.auditor_calibration_stage import AuditorCalibrationStage
from src.utils.logging_setup import get_logger

logger = get_logger("OfflineService")

class OfflineService(QThread):
    """
    Service responsible for Phase 1: Offline Bootstrap.
    
    Refactored Architecture (SOLID - SRP & OCP):
    - Acts exclusively as an Orchestrator / UI Thread Manager.
    - Delegates the heavy lifting to specialized Stage classes.
    - Shares state through a common context dictionary.
    """

    # Signals for UI Updates
    log_message = pyqtSignal(str)
    bootstrap_finished = pyqtSignal()
    progress_update = pyqtSignal(int)

    def __init__(self, app_state: AppState = None):
        """
        Args:
            app_state: The central application state injected from BootstrapPhase.
        """
        super().__init__()
        self.app_state = app_state
        self.running = True
        
        from src.storage.path_scaffolder import PathScaffolder
        scaffolder = PathScaffolder()
        self.home_dir = str(scaffolder.home)
        self.synapse_root = scaffolder.get_project_root()
        self.datalake_dir = str(scaffolder.datalake_dir)
        self.base_dir = scaffolder.get_datalake_base_path()
        self.golden_dir = scaffolder.get_datalake_golden_path()
        self.config_dir = scaffolder.get_config_path()

    def run(self):
        """Main execution pipeline."""
        self._handle_log("[OfflineService] 🟢 Starting Offline Service Thread...")
        self.progress_update.emit(0)
        
        try:
            self._ensure_directories()
            
            # Setup Shared Context (Shared memory for the stages)
            shared_context = {
                "base_dir": self.base_dir,
                "golden_dir": self.golden_dir,
                "config_dir": self.config_dir,
                "golden_path": os.path.join(self.golden_dir, "golden_v1.parquet"),
                "json_path": os.path.join(self.config_dir, "peak_schedule.json"),
                "linguist_checkpoint_path": os.path.join(self.config_dir, "linguist_calibrated.json"),
                "auditor_checkpoint_path": os.path.join(self.config_dir, "auditor_calibrated.pth"),
                "ontology_checkpoint_path": os.path.join(self.config_dir, "ontology.safetensors")
            }
            
            # --- MASTER SKIP LOCK ---
            if self._check_master_lock(shared_context):
                self._handle_log("[OfflineService] 🏆 All Phase 1 artifacts found and validated (Golden, JSON, Calibrations, Ontology).")
                self._handle_log("[OfflineService] ⏩ Skipping Offline Phase entirely.")
                self.progress_update.emit(100)
                self.bootstrap_finished.emit()
                return

            # Initialize Pipeline Stages
            stages = [
                SanitizationStage(self.synapse_root, self._handle_log, self._handle_progress, self._check_stop),
                ClassificationStage(self.synapse_root, self._handle_log, self._handle_progress, self._check_stop),
                LinguistCalibrationStage(self.synapse_root, self._handle_log, self._handle_progress, self._check_stop),
                AuditorCalibrationStage(self.synapse_root, self._handle_log, self._handle_progress, self._check_stop)
            ]
            
            # Execute Pipeline sequentially
            for stage in stages:
                success = stage.execute(shared_context)
                if not success:
                    # Break the pipeline if a stage fails or is interrupted by the user
                    break

        except Exception as e:
            self._handle_log(f"[OfflineService] ❌ CRITICAL ERROR: {str(e)}")
            traceback.print_exc()
        finally:
            self.bootstrap_finished.emit()

    def _ensure_directories(self):
        """Creates the necessary folder structure if it does not exist."""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.golden_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

    def _check_master_lock(self, ctx: dict) -> bool:
        """Verifies if all target artifacts are already generated and valid."""
        golden_valid = os.path.exists(ctx["golden_path"]) and os.path.getsize(ctx["golden_path"]) > 0
        json_valid = os.path.exists(ctx["json_path"]) and os.path.getsize(ctx["json_path"]) > 0
        linguist_valid = os.path.exists(ctx["linguist_checkpoint_path"]) and os.path.getsize(ctx["linguist_checkpoint_path"]) > 0
        auditor_valid = os.path.exists(ctx["auditor_checkpoint_path"]) and os.path.getsize(ctx["auditor_checkpoint_path"]) > 0
        ontology_valid = (
            "ontology_checkpoint_path" in ctx
            and os.path.exists(ctx["ontology_checkpoint_path"])
            and os.path.getsize(ctx["ontology_checkpoint_path"]) > 0
        )
        return golden_valid and json_valid and linguist_valid and auditor_valid and ontology_valid

    def _handle_log(self, message: str):
        """Callback to emit logs from the stages to the UI and persist to session log."""
        logger.info(message)
        self.log_message.emit(message)

    def _handle_progress(self, value: int):
        """Callback to emit progress from the stages to the UI."""
        self.progress_update.emit(value)

    def _check_stop(self) -> bool:
        """Callback to let stages know if the thread was stopped."""
        return not self.running

    def stop(self):
        """Safely flags the thread to stop."""
        self.running = False
