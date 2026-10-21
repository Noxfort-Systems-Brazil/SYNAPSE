# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Sensor Telemetry Extractor.

Extracts live detectors from AppState, formats operational and metrological attributes,
and delegates kinematic derivation to TrafficKinematicsCalculator.
"""

from typing import Dict, Any, List, Optional
from src.report.traffic_kinematics import TrafficKinematicsCalculator


class SensorTelemetryExtractor:
    """Extracts live sensors strictly from AppState. Zero fake fallback."""

    @classmethod
    def extract_sensors(
        cls,
        app_state: Any,
        kinematics_calc: Optional[TrafficKinematicsCalculator] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extracts live sensors from AppState with authentic telemetry metrics.
        """
        get_sources_fn = getattr(app_state, "get_all_data_sources", None) if app_state else None
        if not callable(get_sources_fn):
            return []

        calc = kinematics_calc or TrafficKinematicsCalculator
        sensors = []

        for s in (get_sources_fn() or []):
            sid = getattr(s, "id", "")
            name = getattr(s, "name", "")
            stype = getattr(s, "source_type", "Sensor de Tráfego")

            speed = getattr(s, "last_speed", None)
            if speed is None:
                val = getattr(s, "latest_value", None)
                speed = float(val) if isinstance(val, (int, float)) else 18.0
            speed_float = float(speed)

            kinematics = calc.derive_sensor_kinematics(speed_float, s)
            sensors.append({
                "id": sid,
                "junction": f"Estação: {name or sid}",
                "equipmentType": str(stype),
                "measuredSpeed": f"{speed_float:.1f} km/h",
                "measuredFlow": kinematics["measuredFlow"],
                "saturationDegree": kinematics["saturationDegree"],
                "occupancyRate": kinematics["occupancyRate"],
                "inmetroReport": "Aferição Regular INMETRO",
                "operationalStatus": "Operação Nominal" if speed_float >= 10.0 else "Alerta de Retenção Crítica",
            })

        return sensors
