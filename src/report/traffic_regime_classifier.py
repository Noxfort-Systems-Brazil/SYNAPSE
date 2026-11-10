# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unified Canonical Traffic Regime Classifier.

Implements Rule 3 of the SYNAPSE XAI Report Validation Gate:
- Single canonical function classifying speed and saturation into 4 discrete tiers with intermediate bands.
- Both individual stations and the overall arterial corridor use the exact same logic.
- Generates threshold tables for transparency in municipal documents.
- Always highlights the worst station when corridor metrics rely on network averages.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RegimeTier:
    tier: int
    name: str
    status_label: str
    los_label: str
    speed_range_desc: str
    saturation_range_desc: str
    min_speed: float
    max_speed: float
    min_sat: float
    max_sat: float


class TrafficRegimeClassifier:
    """
    Unified Single Source of Truth for Traffic Regime Classification.
    Complies with Highway Capacity Manual (HCM 7th Ed.) and municipal reporting rules.
    """

    TIERS = [
        RegimeTier(
            tier=1,
            name="Livre / Fluido",
            status_label="Operação Nominal",
            los_label="Nível de Serviço A / B (Fluxo Livre)",
            speed_range_desc="≥ 35,0 km/h",
            saturation_range_desc="< 0,60",
            min_speed=35.0,
            max_speed=999.0,
            min_sat=0.0,
            max_sat=0.60,
        ),
        RegimeTier(
            tier=2,
            name="Estável / Moderado",
            status_label="Fluxo Estável",
            los_label="Nível de Serviço C / D (Escoamento Monitorado)",
            speed_range_desc="20,0 – 34,9 km/h",
            saturation_range_desc="0,60 – 0,74",
            min_speed=20.0,
            max_speed=35.0,
            min_sat=0.60,
            max_sat=0.75,
        ),
        RegimeTier(
            tier=3,
            name="Saturado / Retenção",
            status_label="Alerta de Retenção",
            los_label="Nível de Serviço E (Capacidade Limite / Saturação)",
            speed_range_desc="10,0 – 19,9 km/h",
            saturation_range_desc="0,75 – 0,89",
            min_speed=10.0,
            max_speed=20.0,
            min_sat=0.75,
            max_sat=0.90,
        ),
        RegimeTier(
            tier=4,
            name="Crítico / Retenção Severa",
            status_label="Crítico / Retenção Severa",
            los_label="Nível de Serviço F (Escoamento Forçado / Colapso)",
            speed_range_desc="< 10,0 km/h",
            saturation_range_desc="≥ 0,90",
            min_speed=0.0,
            max_speed=10.0,
            min_sat=0.90,
            max_sat=999.0,
        ),
    ]

    @classmethod
    def classify_by_speed(cls, speed_kmh: float) -> int:
        """Determines tier (1 to 4) solely based on spatial speed."""
        if speed_kmh < 10.0:
            return 4
        elif speed_kmh < 20.0:
            return 3
        elif speed_kmh < 35.0:
            return 2
        return 1

    @classmethod
    def classify_by_saturation(cls, saturation: float) -> int:
        """Determines tier (1 to 4) solely based on degree of saturation."""
        if saturation >= 0.90:
            return 4
        elif saturation >= 0.75:
            return 3
        elif saturation >= 0.60:
            return 2
        return 1

    @classmethod
    def classify(cls, speed_kmh: float, saturation: float) -> RegimeTier:
        """
        Classifies traffic operational state into one of 4 canonical tiers.
        Priority is given to severity (tie-breaker: worst criterion between speed and saturation):
        severity_tier = max(tier_speed, tier_saturation).
        """
        tier_spd = cls.classify_by_speed(speed_kmh)
        tier_sat = cls.classify_by_saturation(saturation)
        worst_tier = max(tier_spd, tier_sat)
        return cls.TIERS[worst_tier - 1]

    @classmethod
    def classify_station(cls, speed_raw: Any, saturation_raw: Any) -> Dict[str, Any]:
        """Classifies a single station from string, float, or formatted values."""
        spd = cls._parse_numeric(speed_raw, default=25.0)
        sat = cls._parse_numeric(saturation_raw, default=0.65)
        tier = cls.classify(spd, sat)
        return {
            "tier": tier.tier,
            "regime_name": tier.name,
            "operational_status": tier.status_label,
            "los_label": tier.los_label,
            "parsed_speed": spd,
            "parsed_saturation": sat,
        }

    @classmethod
    def classify_corridor(
        cls, stations_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classifies overall corridor and identifies the worst station.
        Guarantees that corridor average does NOT mask severe point retention.
        """
        if not stations_metrics:
            default_tier = cls.TIERS[1]
            return {
                "corridor_tier": default_tier.tier,
                "corridor_regime": default_tier.name,
                "corridor_los": default_tier.los_label,
                "average_speed": 25.0,
                "average_saturation": 0.65,
                "worst_station_id": "N/A",
                "worst_station_name": "N/A",
                "worst_station_tier": default_tier.tier,
                "worst_station_speed": 25.0,
                "worst_station_saturation": 0.65,
                "has_divergence": False,
            }

        parsed_stations = []
        for s in stations_metrics:
            sid = s.get("id") or s.get("detectorId") or "SENSOR"
            name = s.get("junction") or s.get("name") or sid
            spd = cls._parse_numeric(s.get("measuredSpeed"), default=25.0)
            raw_sat = s.get("saturationDegree") if s.get("saturationDegree") is not None else s.get("saturation")
            sat = cls._parse_numeric(raw_sat, default=0.65)
            tier = cls.classify(spd, sat)
            parsed_stations.append({
                "id": sid,
                "name": name,
                "speed": spd,
                "saturation": sat,
                "tier": tier,
            })

        avg_spd = sum(p["speed"] for p in parsed_stations) / len(parsed_stations)
        avg_sat = sum(p["saturation"] for p in parsed_stations) / len(parsed_stations)
        corridor_tier = cls.classify(avg_spd, avg_sat)

        # All stations in Tier 4 (Crítico / Retenção Severa)
        critical_stations = [
            p for p in sorted(
                parsed_stations,
                key=lambda x: (x["tier"].tier, -x["speed"], x["saturation"]),
                reverse=True
            )
            if p["tier"].tier == 4
        ]

        # Worst station is the one with the highest tier (4 is most severe), then lowest speed, then highest sat
        worst = max(
            parsed_stations,
            key=lambda x: (x["tier"].tier, -x["speed"], x["saturation"]),
        )

        has_divergence = worst["tier"].tier > corridor_tier.tier
        total_st = len(parsed_stations)
        crit_count = len(critical_stations)

        status_counts = {
            t.tier: sum(1 for p in parsed_stations if p["tier"].tier == t.tier)
            for t in cls.TIERS
        }

        return {
            "corridor_tier": corridor_tier.tier,
            "corridor_regime": corridor_tier.name,
            "corridor_los": corridor_tier.los_label,
            "average_speed": round(avg_spd, 1),
            "average_saturation": round(avg_sat, 2),
            "worst_station_id": worst["id"],
            "worst_station_name": worst["name"],
            "worst_station_tier": worst["tier"].tier,
            "worst_station_regime": worst["tier"].name,
            "worst_station_status": worst["tier"].status_label,
            "worst_station_speed": round(worst["speed"], 1),
            "worst_station_saturation": round(worst["saturation"], 2),
            "has_divergence": has_divergence,
            "total_stations": total_st,
            "critical_stations": critical_stations,
            "critical_count": crit_count,
            "status_counts": status_counts,
        }

    @classmethod
    def get_thresholds_table_markdown(cls) -> str:
        """Returns the normative reference threshold table in Markdown format."""
        lines = [
            "| Nível Operacional | Velocidade Espacial (v) | Grau de Saturação (x) | Nível de Serviço (HCM) | Status de Controle |",
            "| :--- | :---: | :---: | :--- | :--- |",
        ]
        for t in cls.TIERS:
            lines.append(
                f"| **{t.name}** | {t.speed_range_desc} | {t.saturation_range_desc} | {t.los_label.split(' - ')[0]} | {t.status_label} |"
            )
        lines.append("")
        lines.append("> *Critério de desempate operacional: havendo divergência entre os patamares de velocidade e saturação, adota-se o nível de maior gravidade/severidade.*")
        return "\n".join(lines)

    @staticmethod
    def _parse_numeric(val: Any, default: float = 0.0) -> float:
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return float(val)
        try:
            # Extract first number before space or unit (e.g. "18,4 km/h" -> "18,4")
            raw_str = str(val).strip().split()[0].replace(",", ".")
            return float(raw_str)
        except Exception:
            return default
