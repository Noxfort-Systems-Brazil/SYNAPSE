# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/kse_manager.py
# Description: Pure Orchestrator for Kalman State Estimation (SOLID: SRP / Clean Arch).

import time
import traceback
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, Qt

from src.domain.app_state import AppState
from src.services.historical_manager import HistoricalManager
from src.kse.meh_bridge import MEHBridge
from src.kse.packet_builder import PacketBuilder
from src.managers.kse.transmission_gate import CarinaTransmissionGate


class KSEManager(QObject):
    """
    Kalman State Estimation (KSE) Manager - Pure Physics Engine Orchestrator.

    Coordinates:
    - MEH baseline management (MEHBridge)
    - Transmission gate validation (CarinaTransmissionGate)
    - HFT packet synthesis (PacketBuilder)
    - Elastic window timing logic (QTimer 10ms monitor)
    """

    # Output: The physics packet ready for HFT transmission
    data_ready_for_transmission = pyqtSignal(dict)

    # Telemetry
    log_message = pyqtSignal(str)
    mode_changed = pyqtSignal(str)  # "REALTIME" or "HISTORICAL"

    def __init__(self, app_state: AppState, historical_manager: Optional[HistoricalManager] = None):
        super().__init__()
        self.app_state = app_state

        # Dependencies
        self._historical_manager = historical_manager if historical_manager is not None else HistoricalManager(app_state)
        self._meh_bridge = MEHBridge(self._historical_manager)

        # State
        self.running = False
        self.current_mode = "REALTIME"

        # Timing
        self.last_sensor_update_time = 0.0
        self.last_transmission_time = 0.0
        self.has_new_processed_data = False

        # Data
        self.last_known_state = {}
        self._has_valid_data = False

        # Transmission Gate
        self.is_warmup_complete = False
        self._rejection_warned = False

        # Elastic Window Parameters
        self.min_window_ms = 0.150  # 150ms (~6.6 Hz)
        self.sensor_timeout_threshold = 3.0  # 3.0s without data -> HISTORICAL

        # Monitor Timer (10ms resolution)
        self.monitor = QTimer(self)
        self.monitor.setTimerType(Qt.TimerType.PreciseTimer)
        self.monitor.timeout.connect(self._check_elastic_window)

    def start(self):
        if self.running:
            return
        self.running = True
        self.last_transmission_time = time.time()
        self.is_warmup_complete = False
        self._has_valid_data = False
        self._rejection_warned = False

        self._activate_meh_baseline()
        self.monitor.start(10)

    def stop(self):
        self.running = False
        self.monitor.stop()
        self.is_warmup_complete = False
        self._has_valid_data = False
        self._rejection_warned = False
        self.log_message.emit("[KSE] Physics Engine Stopped.")

    def _activate_meh_baseline(self):
        """Loads MEH data into RAM as the initial operational baseline."""
        meh_data = self._meh_bridge.load_baseline()
        if meh_data:
            self.last_known_state = meh_data
            self.has_new_processed_data = True
            self._has_valid_data = True
            self.current_mode = "HISTORICAL"
            self.mode_changed.emit("HISTORICAL")
            self.log_message.emit(
                f"[KSE] ⚡ Baseline MEH carregada na RAM ({len(meh_data)} edges). "
                f"Aguardando validação de pelo menos 1 sensor LOCAL e 1 sensor GLOBAL antes de iniciar transmissão para a CARINA."
            )
        else:
            self.log_message.emit(
                "[KSE] ⚠️ Physics Engine Started. MEH empty. Aguardando validação de sensores..."
            )

    def _check_carina_transmission_gate(self) -> bool:
        """Evaluates whether transmission to CARINA is authorized."""
        authorized, warmup_complete, rejection_warned, msg = CarinaTransmissionGate.evaluate(
            app_state=self.app_state,
            is_warmup_complete=self.is_warmup_complete,
            rejection_warned=self._rejection_warned
        )
        self.is_warmup_complete = warmup_complete
        self._rejection_warned = rejection_warned

        if authorized:
            self._has_valid_data = True

        if msg:
            self.log_message.emit(msg)

        return authorized

    @pyqtSlot(dict)
    def sync_with_reality(self, sensor_snapshot: dict):
        """Synchronizes KSE with reality frame from inference engine."""
        self.last_sensor_update_time = time.time()
        self.last_known_state = sensor_snapshot
        self.has_new_processed_data = True

        self._check_carina_transmission_gate()

        if self.is_warmup_complete and sensor_snapshot:
            self._has_valid_data = True

        if self.running:
            self._check_elastic_window()

        if self.is_warmup_complete and self.current_mode != "REALTIME":
            self.current_mode = "REALTIME"
            self._meh_bridge.deactivate()
            self.mode_changed.emit("REALTIME")
            self.log_message.emit("[KSE] 🟢 Sensor signal restored. Mode: REALTIME.")

    @pyqtSlot()
    def _check_elastic_window(self):
        """The core timing logic. Runs every 10ms."""
        if not self.running:
            return

        if not self._check_carina_transmission_gate():
            return

        try:
            now = time.time()
            dt_transmission = now - self.last_transmission_time
            dt_sensor = now - self.last_sensor_update_time

            if self.current_mode == "HISTORICAL":
                fresh_data = self._meh_bridge.refresh_if_needed()
                if fresh_data:
                    self.last_known_state = fresh_data
                    self.has_new_processed_data = True

            if not self._has_valid_data:
                return

            if dt_transmission < self.min_window_ms:
                return

            if self.has_new_processed_data:
                packet_source = self.current_mode.lower()
                payload_data = self.last_known_state
            else:
                packet_source = "kse_dead_reckoning"
                payload_data = PacketBuilder.extrapolate(self.last_known_state, dt_transmission)

            if dt_sensor > self.sensor_timeout_threshold:
                if self.current_mode == "REALTIME":
                    self.current_mode = "HISTORICAL"
                    self._meh_bridge.is_active = True
                    self.mode_changed.emit("HISTORICAL")
                    self.log_message.emit(
                        f"[KSE] ⚠️ Signal Lost ({dt_sensor:.1f}s). Mode: HISTORICAL. MEH fallback active."
                    )

            packet = PacketBuilder.build(payload_data, packet_source, self.app_state)
            if packet:
                self.data_ready_for_transmission.emit(packet)

            self.last_transmission_time = time.time()
            self.has_new_processed_data = False

        except Exception as e:
            self.log_message.emit(f"[KSE] ❌ Monitor Error: {e}")
            traceback.print_exc()
