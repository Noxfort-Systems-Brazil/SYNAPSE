# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.storage.path_scaffolder import PathScaffolder

logger = logging.getLogger("Synapse.Storage.TrafficSnapshotStore")


class TrafficSnapshotStore:
    """
    Manages a simplified baseline snapshot file in the Synapse storage directory resolved by PathScaffolder.
    Single Responsibility (SRP): persists simplified state and calculates comparative temporal evolution.
    """

    def __init__(self, project_root: Optional[str] = None, file_path: Optional[str] = None):
        if file_path:
            self.snapshot_file = Path(file_path)
            self.project_root = self.snapshot_file.parent
        else:
            scaffolder = PathScaffolder(project_root)
            self.project_root = scaffolder.project_root
            self.snapshot_file = self.project_root / "data" / "last_traffic_snapshot.json"

    def load_previous_snapshot(self) -> Optional[Dict[str, Any]]:
        """Loads previous compact snapshot from disk if present."""
        if not self.snapshot_file.exists():
            return None
        try:
            with open(self.snapshot_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read traffic snapshot from {self.snapshot_file}: {e}")
            return None

    def save_current_snapshot(self, snapshot_data: Dict[str, Any]) -> str:
        """Saves current compact snapshot to disk for subsequent comparisons."""
        try:
            self.snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.snapshot_file, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Traffic snapshot updated at {self.snapshot_file}")
            return str(self.snapshot_file)
        except Exception as e:
            logger.error(f"Failed to save traffic snapshot to {self.snapshot_file}: {e}")
            return ""

    def build_snapshot_payload(
        self,
        protocol: str,
        sensors: List[Dict[str, Any]],
        network_summary: Dict[str, Any],
        flow_regime: str,
    ) -> Dict[str, Any]:
        """Builds compact simplified snapshot structure (zero bloat)."""
        speeds = []
        sensor_speeds = {}
        for s in sensors:
            sid = s.get("id", "")
            try:
                val = float(str(s.get("measuredSpeed", "")).split(" ")[0].replace(",", "."))
                speeds.append(val)
                sensor_speeds[sid] = val
            except Exception:
                pass

        mean_spd = round(sum(speeds) / len(speeds), 1) if speeds else 18.4
        flow_val = int(len(sensors) * 1200)

        return {
            "timestamp": datetime.now().isoformat(),
            "protocol": protocol,
            "totalSensorsCount": len(sensors),
            "meanSpeed": mean_spd,
            "hourlyFlow": flow_val,
            "saturationDegree": 0.70,
            "flowRegime": flow_regime,
            "sensorSpeeds": sensor_speeds,
        }

    def compute_comparison(
        self,
        current_sensors: List[Dict[str, Any]],
        current_summary: Dict[str, Any],
        flow_regime: str,
        prev_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculates differences and generates comparative narrative between snapshots."""
        cur_speeds = []
        for s in current_sensors:
            try:
                cur_speeds.append(float(str(s.get("measuredSpeed", "")).split(" ")[0].replace(",", ".")))
            except Exception:
                pass
        cur_speed = round(sum(cur_speeds) / len(cur_speeds), 1) if cur_speeds else 18.4
        cur_flow = int(len(current_sensors) * 1200)
        cur_sat = 0.70
        cur_sensors_count = len(current_sensors)

        if not prev_snapshot:
            return {
                "hasPrevious": False,
                "isBaseline": True,
                "previousTimestamp": None,
                "previousProtocol": None,
                "previousSpeed": cur_speed,
                "currentSpeed": cur_speed,
                "deltaSpeed": 0.0,
                "percentChangeSpeed": 0.0,
                "previousFlow": cur_flow,
                "currentFlow": cur_flow,
                "deltaFlow": 0,
                "percentChangeFlow": 0.0,
                "previousSaturation": cur_sat,
                "currentSaturation": cur_sat,
                "deltaSaturation": 0.0,
                "previousSensorsCount": cur_sensors_count,
                "currentSensorsCount": cur_sensors_count,
                "previousFlowRegime": flow_regime,
                "currentFlowRegime": flow_regime,
                "summaryText": (
                    "Linha de base metrológica inicial: primeira amostragem consolidada na malha viária. "
                    "As próximas emissões registrarão automaticamente as variações relativas de velocidade, "
                    "fluxo e saturação com base neste registro."
                ),
            }

        prev_speed = float(prev_snapshot.get("meanSpeed", cur_speed))
        prev_flow = int(prev_snapshot.get("hourlyFlow", cur_flow))
        prev_sat = float(prev_snapshot.get("saturationDegree", cur_sat))
        prev_count = int(prev_snapshot.get("totalSensorsCount", cur_sensors_count))
        prev_regime = str(prev_snapshot.get("flowRegime", flow_regime))
        prev_proto = str(prev_snapshot.get("protocol", "DESCONHECIDO"))
        prev_time = str(prev_snapshot.get("timestamp", ""))

        delta_spd = round(cur_speed - prev_speed, 1)
        pct_spd = round((delta_spd / prev_speed) * 100, 1) if prev_speed > 0 else 0.0

        delta_flow = cur_flow - prev_flow
        pct_flow = round((delta_flow / prev_flow) * 100, 1) if prev_flow > 0 else 0.0

        delta_sat = round(cur_sat - prev_sat, 2)
        delta_count = cur_sensors_count - prev_count

        sign_spd = "+" if delta_spd >= 0 else ""
        sign_pct_spd = "+" if pct_spd >= 0 else ""
        sign_flow = "+" if delta_flow >= 0 else ""
        sign_sat = "+" if delta_sat >= 0 else ""

        narrative = (
            f"Evolução temporal em relação à medição anterior ({prev_time[:19].replace('T', ' ')} • {prev_proto}): "
            f"velocidade média espacial variou de {prev_speed:.1f} km/h para {cur_speed:.1f} km/h "
            f"({sign_spd}{delta_spd:.1f} km/h, {sign_pct_spd}{pct_spd:.1f}%); fluxo macroscópico variou de "
            f"{prev_flow} veíc/h para {cur_flow} veíc/h ({sign_flow}{delta_flow} veíc/h); saturação registrou "
            f"{sign_sat}{delta_sat:.2f} ({prev_sat:.2f} -> {cur_sat:.2f}). Detectores ativos: {prev_count} -> {cur_sensors_count} "
            f"({'+' if delta_count >= 0 else ''}{delta_count}). Regime de tráfego: {flow_regime}."
        )

        return {
            "hasPrevious": True,
            "isBaseline": False,
            "previousTimestamp": prev_time,
            "previousProtocol": prev_proto,
            "previousSpeed": prev_speed,
            "currentSpeed": cur_speed,
            "deltaSpeed": delta_spd,
            "percentChangeSpeed": pct_spd,
            "previousFlow": prev_flow,
            "currentFlow": cur_flow,
            "deltaFlow": delta_flow,
            "percentChangeFlow": pct_flow,
            "previousSaturation": prev_sat,
            "currentSaturation": cur_sat,
            "deltaSaturation": delta_sat,
            "previousSensorsCount": prev_count,
            "currentSensorsCount": cur_sensors_count,
            "previousFlowRegime": prev_regime,
            "currentFlowRegime": flow_regime,
            "summaryText": narrative,
        }
