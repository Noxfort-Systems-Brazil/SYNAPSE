# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any


class KinematicExtrapolator:
    """
    Single Responsibility: Projects traffic metrics forward in time using
    kinematic physics velocities (Kalman / Dead Reckoning).
    Extracted from PacketBuilder to isolate kinematic projection from serialization.
    """

    @staticmethod
    def extrapolate(base_state: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Projects traffic metrics forward using KSE physics velocities.
        Used for dead reckoning when the neural engine is slow.

        Args:
            base_state: Last known state dict mapping source_id -> metrics.
            dt: Time delta in seconds since last transmission.

        Returns:
            Extrapolated state dict.
        """
        extrapolated: Dict[str, Any] = {}
        for source_id, metrics in base_state.items():
            new_metrics = dict(metrics)

            if "physics" in metrics:
                v = float(metrics["physics"].get("v", 0.0))
                current_val = float(metrics.get("value", 10.0))
                new_metrics["value"] = max(0.1, current_val + (v * dt))

            if "density" in metrics:
                new_metrics["density"] = max(0.1, float(metrics.get("density", 10.0)))

            if "speed" in metrics:
                s = float(metrics.get("speed", 40.0))
                new_metrics["speed"] = s if s > 0.5 else 40.0

            extrapolated[source_id] = new_metrics

        return extrapolated
