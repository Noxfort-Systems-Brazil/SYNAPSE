# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Callable, Dict, Optional


class SensorUnitConverter:
    """
    Stateless, high-performance mathematical converter for physical sensor units to the
    International System of Units (SI: m/s for speed, veh/s for flow).

    Adheres to SOLID Principles:
    - [SRP] Single Responsibility: Applies canonical SI mathematical conversion rules in O(1).
    - [OCP] Open/Closed: Extensible canonical rule map without modifying caller ingestion pipelines.
    - [Stateless]: Holds zero sensor-specific state, IDs, or storage.
    - [Anti-Hallucination]: Unconvertible or unknown units return None to enforce immediate discard.
    """

    # Canonical Conversion Rules (1 to 5)
    RULES: Dict[int, Callable[[float], float]] = {
        1: lambda v: float(v) / 3.6,        # km/h  -> m/s
        2: lambda v: float(v) * 0.44704,    # mph   -> m/s
        3: lambda v: float(v) / 3600.0,     # veh/h -> veh/s
        4: lambda v: float(v) / 60.0,       # veh/min -> veh/s
        5: lambda v: float(v),              # Direct SI (m/s, veh/s) or Identity
    }

    @classmethod
    def convert(cls, value: float, rule_id: Optional[int] = 5) -> Optional[float]:
        """
        Converts a raw numeric sensor reading to SI units in O(1).
        Returns None if rule_id is unmapped or None, signaling that the reading must be discarded
        to prevent downstream neural/Kalman filter hallucination.
        """
        if rule_id is None or rule_id not in cls.RULES:
            return None
        transform = cls.RULES[rule_id]
        return transform(value)

    @classmethod
    def rule_for_unit(cls, unit: Optional[str]) -> Optional[int]:
        """
        Maps a semantic unit string (e.g. from SemanticClassifier / Linguist) to a canonical rule ID.
        Returns None if the unit is outside the convertible traffic SI scope.
        """
        if not unit:
            return None

        u = unit.strip().lower()
        if u in ("km/h", "kmh", "km/hr"):
            return 1
        if u in ("mph", "mi/h"):
            return 2
        if u in ("veh/h", "veic/h", "vph"):
            return 3
        if u in ("veh/min", "veic/min", "vpm"):
            return 4
        if u in ("m/s", "ms", "mps", "veh/s", "veic/s", "vps", "veh", "veic", "count", "vehicles", "veiculos"):
            return 5

        # Outside convertible physical traffic domain -> discard
        return None

    @classmethod
    def is_supported_unit(cls, unit: Optional[str]) -> bool:
        """Checks if a unit can be safely converted to SI without hallucination."""
        return cls.rule_for_unit(unit) is not None
