# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import TYPE_CHECKING
from PyQt6.QtCore import QObject, pyqtSignal

from src.domain.app_state import AppState
from src.domain.entities import SourceType
from src.utils.logging_setup import get_logger

logger = get_logger("RuntimePhase")

# --- Internal Components (The "Split" Logic) ---
from src.phases.runtime_connector import RuntimeConnector
from src.phases.runtime_launcher import RuntimeLauncher

if TYPE_CHECKING:
    from src.services.fenix_service import FenixService

class RuntimePhase(QObject):
    """
    Orchestrator for Phase 2: Online Operation.
    
    Location: src/phases/runtime_phase.py
    
    Refactored V37 (Component Split):
    - Acts as a FACADE for the Runtime subsystem.
    - Coordinates 'RuntimeConnector' (Network) and 'RuntimeLauncher' (Compute).
    - Bridges signals between Network, AI, and the Main Controller.
    - Does NOT contain complex logic itself; only wiring.
    """

    # --- PUBLIC SIGNALS (Consumed by SystemController) ---
    log_message = pyqtSignal(str)
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    system_started = pyqtSignal()
    system_stopped = pyqtSignal()
    
    # Data Streams
    engine_data_processed = pyqtSignal(dict)
    engine_global_results = pyqtSignal(dict)
    kinetic_data_ready = pyqtSignal(dict)
    
    # Advanced Streams
    audit_update = pyqtSignal(bool, float, float, list)
    linguist_update = pyqtSignal(str, str, float)
    drift_update = pyqtSignal(str, dict)
    xai_result_received = pyqtSignal(dict)

    def __init__(self, app_state: AppState, fenix_service: 'FenixService'):
        super().__init__()
        
        self.app_state = app_state
        self.fenix_service = fenix_service
        
        # 1. Initialize Sub-Components
        self.connector = RuntimeConnector(app_state)
        self.launcher = RuntimeLauncher(app_state, fenix_service)
        
        # 2. Wire Internal Logic (The "Glue")
        self._wire_internals()
        
        # 3. Wire External Outputs (Bubbling up signals)
        self._wire_outputs()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def start(self) -> bool:
        """Entry point: Validates live sources, starts compute & ingestion, and arms HFT upon 1+1 rule fulfillment."""
        # Mandatory Check: at least 1 LOCAL + 1 GLOBAL live source registered
        all_sources = self.app_state.get_all_data_sources()
        
        live_sources = [
            s for s in all_sources
            if s.source_type != SourceType.SUMO_NET_XML
            and not (isinstance(s.connection_string, str) and s.connection_string.endswith(".parquet"))
            and "Historical Base" not in s.name
        ]
        
        has_local = any(s.is_local for s in live_sources)
        has_global = any(not s.is_local for s in live_sources)
        
        if not has_local or not has_global:
            missing = []
            if not has_local:
                missing.append("LOCAL (sensor/camera/radar)")
            if not has_global:
                missing.append("GLOBAL (Waze/TomTom API)")
            error_msg = f"❌ Runtime Aborted: Missing LIVE data sources: {', '.join(missing)}. Both LOCAL and GLOBAL sources are MANDATORY."
            self.log_message.emit(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        # Security & Resilience Guard: Local sensors require active DuckDNS
        if has_local:
            try:
                from src.database.db_settings_manager import DatabaseSettingsManager
                duck_cfg = DatabaseSettingsManager().load_duckdns_settings()
                if not duck_cfg.get("enabled", False) or not str(duck_cfg.get("domain", "")).strip():
                    error_msg = (
                        "❌ Operação Abortada: Sensores Locais exigem DuckDNS configurado e ativo "
                        "para ingestão remota resiliente. Acesse Configurações > Acesso Remoto (DuckDNS)."
                    )
                    self.log_message.emit(error_msg)
                    self.error_occurred.emit(error_msg)
                    return False
            except Exception as e:
                logger.warning(f"[RuntimePhase] Falha ao verificar status do DuckDNS: {e}")

        logger.info("🚀 [Fase 2: Operação Online] Ativando ingestão de dados ao vivo:")
        import os
        gw_port = int(os.getenv("SYNAPSE_GATEWAY_PORT", "8081"))
        logger.info(f"   📡 Sensores Locais ({sum(1 for s in live_sources if s.is_local)}): Gateway HTTP ativo escutando POSTs na porta {gw_port}.")
        logger.info(f"   ☁️ Sensores Globais ({sum(1 for s in live_sources if not s.is_local)}): Polling ativo para APIs externas.")

        # 1. Start compute & ingestion engines first (SensorGateway + IngestionWorker + Linguist)
        self.launcher.start_engines()

        # 2. Activate FENIX Watchdog Monitoring in Phase 2 (Online Operation)
        if self.fenix_service:
            self.fenix_service.activate_monitoring()

        # 3. Evaluate 1+1 Rule for HFT Network Transport
        self._check_one_plus_one_and_connect(initial=True)
        return True

    def _is_one_plus_one_satisfied(self) -> bool:
        """Checks if at least 1 LOCAL and at least 1 GLOBAL sensor are ACTIVE and validated."""
        from src.domain.entities import SourceStatus
        all_sources = self.app_state.get_all_data_sources()
        live_sources = [
            s for s in all_sources
            if s.source_type != SourceType.SUMO_NET_XML
            and not (isinstance(s.connection_string, str) and s.connection_string.endswith(".parquet"))
            and "Historical Base" not in s.name
        ]
        has_active_local = any(s.is_local and s.status == SourceStatus.ACTIVE for s in live_sources)
        has_active_global = any(not s.is_local and s.status == SourceStatus.ACTIVE for s in live_sources)
        return has_active_local and has_active_global

    def _check_one_plus_one_and_connect(self, initial: bool = False):
        """Monitors 1+1 rule compliance before opening HFT gRPC channel to CARINA."""
        if self.connector.is_connecting or (self.connector.hft_worker and self.connector.hft_worker.isRunning()):
            return

        if self._is_one_plus_one_satisfied():
            logger.info("🎯 [Regra 1+1] ✅ Regra 1+1 cumprida com sucesso! Pelo menos 1 sensor Local e 1 Global estão ATIVOS e validados.")
            logger.info("🔗 [HFT.Transport] Iniciando conexão gRPC com CARINA (localhost:50051)...")
            self.connector.start_connection()
        else:
            if initial:
                logger.info("⏳ [Regra 1+1] Aguardando validação dos sensores (mínimo 1 Local + 1 Global ATIVO)... O canal gRPC (localhost:50051) permanecerá FECHADO até o cumprimento da regra.")

    def stop(self):
        """Stops both network and compute layers."""
        if self.fenix_service:
            self.fenix_service.deactivate_monitoring()
        self.connector.stop_connection()
        self.launcher.stop_engines()
        self.system_stopped.emit()

    def handle_command(self, command_type: str, payload: object = None):
        """Delegates commands to the appropriate component (mostly Launcher)."""
        self.launcher.handle_command(command_type, payload)

    # =========================================================================
    # WIRING LOGIC
    # =========================================================================

    def _wire_internals(self):
        """Connects internal event hooks."""
        # Data Pipeline: Physics Packet Ready -> Send via Network
        self.launcher.packet_ready_to_send.connect(self.connector.send_packet)
        
        # When Linguist updates/promotes or source updates in AppState, re-check 1+1 rule
        self.launcher.linguist_update.connect(lambda *_: self._check_one_plus_one_and_connect())
        self.app_state.data_source_added.connect(lambda *_: self._check_one_plus_one_and_connect())

        # Bind FENIX fallback signal to dedicated transmitter channel if configured
        self.connector.transmitter_channel_configured.connect(self._on_transmitter_channel_configured)

    def _on_transmitter_channel_configured(self, emergency_flag: Any):
        """Binds dedicated transmitter emergency event to FENIX fallback signal."""
        if self.fenix_service and emergency_flag is not None:
            self.fenix_service.bind_transmitter_emergency_flag(emergency_flag)

    def _wire_outputs(self):
        """Connects sub-components signals to this Facade's signals."""
        
        # --- From Connector ---
        self.connector.log_message.connect(self.log_message)
        self.connector.status_message.connect(self.status_message)
        self.connector.connection_failed.connect(self.error_occurred)
        
        # --- From Launcher ---
        self.launcher.log_message.connect(self.log_message)
        self.launcher.error_occurred.connect(self.error_occurred)
        self.launcher.engines_started.connect(self.system_started)
        
        # Data Streams
        self.launcher.engine_data_processed.connect(self.engine_data_processed)
        self.launcher.engine_global_results.connect(self.engine_global_results)
        self.launcher.kinetic_data_ready.connect(self.kinetic_data_ready)
        
        # Advanced Streams
        self.launcher.audit_update.connect(self.audit_update)
        self.launcher.linguist_update.connect(self.linguist_update)
        self.launcher.drift_update.connect(self.drift_update)
        self.launcher.xai_result_received.connect(self.xai_result_received)
