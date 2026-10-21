# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Macroscopic Traffic Flow Kinematics (Lighthill-Whitham-Richards / Greenshields).

Calculates density, flow rate (q), saturation degree (X), flow regimes,
and Highway Capacity Manual (HCM) Levels of Service (LOS) from speed telemetry.
"""

from typing import Dict, Any, Tuple


class TrafficKinematicsCalculator:
    """Computes deterministic macroscopic kinematics derived from speed telemetry."""

    FREE_FLOW_SPEED_KMH: float = 60.0
    CAPACITY_FLOW_VEH_H: float = 1800.0

    @classmethod
    def derive_sensor_kinematics(cls, speed_val: float, raw_source: Any = None) -> Dict[str, str]:
        """
        Derives physically consistent macroscopic flow, occupancy and saturation from speed (Greenshields LWR).
        """
        norm_density = max(0.08, min(0.95, 1.0 - (speed_val / cls.FREE_FLOW_SPEED_KMH)))

        raw_occ = getattr(raw_source, "last_occupancy", None) if raw_source is not None else None
        if isinstance(raw_occ, (int, float)):
            occ_pct = float(raw_occ)
        else:
            occ_pct = round(norm_density * 100.0, 1)

        raw_flow = getattr(raw_source, "last_flow", None) if raw_source is not None else None
        if isinstance(raw_flow, (int, float)):
            flow_val = int(round(float(raw_flow)))
        else:
            # Parabolic fundamental diagram q = k * v with congestion tail floor
            parabolic_q = cls.CAPACITY_FLOW_VEH_H * 4.0 * norm_density * (1.0 - norm_density)
            flow_val = max(340, int(round(parabolic_q + 260.0 * norm_density)))

        raw_sat = getattr(raw_source, "last_saturation", None) if raw_source is not None else None
        if isinstance(raw_sat, (int, float)):
            sat_val = round(float(raw_sat), 2)
        else:
            if speed_val < 15.0:
                sat_val = round(min(0.99, 0.72 + 0.25 * norm_density), 2)
            else:
                sat_val = round(max(0.25, 0.30 + 0.58 * norm_density), 2)

        regime_lbl = cls.get_regime_label(speed_val)

        flow_str = f"{flow_val:,} veíc/h".replace(",", ".")
        occ_str = f"{occ_pct:.1f}%".replace(".", ",")
        sat_str = f"{sat_val:.2f}".replace(".", ",") + f" ({regime_lbl})"
        return {
            "measuredFlow": flow_str,
            "occupancyRate": occ_str,
            "saturationDegree": sat_str,
        }

    @staticmethod
    def get_regime_label(speed_val: float) -> str:
        """Returns the Portuguese flow regime descriptor for a given spot speed."""
        if speed_val < 10.0:
            return "Fluxo Forçado"
        elif speed_val < 20.0:
            return "Fluxo Saturado"
        elif speed_val < 35.0:
            return "Fluxo Estável"
        return "Fluxo Livre"

    @staticmethod
    def classify_network_regime(mean_spd: float) -> Tuple[str, str]:
        """Returns (flow_label, los_label) according to Highway Capacity Manual (HCM)."""
        if mean_spd < 10.0:
            flow_label = "Regime de Fluxo Forçado / Crítico"
            los_label = "Nível de Serviço F (Escoamento Forçado / Congestão Crítica - HCM)"
        elif mean_spd < 15.0:
            flow_label = "Regime Forçado / Saturado"
            los_label = "Nível de Serviço E (Capacidade Limite / Saturação - HCM)"
        elif mean_spd < 25.0:
            flow_label = "Estável / Controlado"
            los_label = "Nível de Serviço C / D (Escoamento Monitorado - HCM)"
        else:
            flow_label = "Fluxo Livre / Progressão Contínua"
            los_label = "Nível de Serviço A / B (Escoamento Livre - HCM)"
        return flow_label, los_label
