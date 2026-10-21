# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging_setup import get_logger

logger = get_logger("AdaptivePoller")


@dataclass
class SourcePollingState:
    """Represents the real-time dynamic polling state for a single external data source."""
    source_id: str
    current_interval: float
    is_quarantine: bool = False
    last_payload_hash: Optional[str] = None
    last_metric_value: Optional[float] = None
    adjustment_count: int = 0
    stable_cycles: int = 0
    volatile_cycles: int = 0


class AdaptivePollingController:
    """
    Dynamic Polling Rate Controller (SOLID: SRP).
    
    Evaluates real-time volatility and provider caching for external/global sources
    within a bounded interval window [min_interval_s, max_interval_s] (typically 60s to 300s).
    
    Principles:
    1. Provider Stagnation / Redundancy (Identical Hash):
       If the API returns the exact same payload as before, the provider hasn't updated its data.
       Gradually increases interval (+step_up_s) up to max_interval_s to preserve API quota.
    2. High Volatility / Sudden Congestion (|Δv| >= volatility_threshold):
       If speed or flow shifts significantly (>= 15%), immediately contracts to min_interval_s (60s)
       to provide high-resolution real-time visibility.
    3. Low Volatility / Calm Traffic (|Δv| <= stable_threshold):
       Increases interval smoothly (+step_up_s) up to max_interval_s.
    4. Quarantine Preservation:
       If the source is quarantined, operates at a fast probe interval (quarantine_interval_s = 10s)
       for expedited health recovery evaluation.
    """

    METRIC_KEYWORDS: List[str] = [
        "currentspeed",
        "speed",
        "velocity",
        "flow",
        "traffic",
        "speedkmh",
        "speed_kmh",
        "speed_val",
        "traveltime",
        "delay",
    ]

    def __init__(
        self,
        min_interval_s: float = 60.0,
        max_interval_s: float = 300.0,
        step_up_s: float = 30.0,
        volatility_threshold: float = 0.15,
        stable_threshold: float = 0.05,
        quarantine_interval_s: float = 10.0,
    ):
        self.min_interval_s = min_interval_s
        self.max_interval_s = max_interval_s
        self.step_up_s = step_up_s
        self.volatility_threshold = volatility_threshold
        self.stable_threshold = stable_threshold
        self.quarantine_interval_s = quarantine_interval_s
        self._states: Dict[str, SourcePollingState] = {}

    def register_source(
        self,
        source_id: str,
        is_quarantine: bool = False,
        initial_interval: Optional[float] = None,
    ) -> float:
        """
        Registers or resets a polling source. Returns the initial effective interval.
        """
        if is_quarantine:
            interval = self.quarantine_interval_s
        elif initial_interval is not None:
            interval = max(self.min_interval_s, min(self.max_interval_s, initial_interval))
        else:
            interval = self.min_interval_s

        self._states[source_id] = SourcePollingState(
            source_id=source_id,
            current_interval=interval,
            is_quarantine=is_quarantine,
        )
        return interval

    def unregister_source(self, source_id: str) -> None:
        """Removes source tracking state."""
        self._states.pop(source_id, None)

    def get_interval(self, source_id: str) -> float:
        """Gets the current effective polling interval for a source."""
        state = self._states.get(source_id)
        if state is None:
            return self.min_interval_s
        return state.current_interval

    def get_state(self, source_id: str) -> Optional[SourcePollingState]:
        """Returns the internal state object for introspection/telemetry."""
        return self._states.get(source_id)

    def evaluate_packet(
        self,
        source_id: str,
        payload: Any,
        is_quarantine: bool = False,
    ) -> Tuple[float, bool]:
        """
        Analyzes an incoming packet payload and returns (new_interval, has_changed).
        
        Args:
            source_id: Unique identifier of the data source.
            payload: Raw or parsed packet payload.
            is_quarantine: Whether the source is currently in quarantine.
            
        Returns:
            Tuple of (new_interval_seconds, has_interval_changed).
        """
        state = self._states.get(source_id)
        if state is None:
            interval = self.register_source(source_id, is_quarantine=is_quarantine)
            state = self._states[source_id]

        prev_interval = state.current_interval

        # 1. Quarantine override
        if is_quarantine or state.is_quarantine:
            state.is_quarantine = is_quarantine
            if state.current_interval != self.quarantine_interval_s:
                state.current_interval = self.quarantine_interval_s
                state.adjustment_count += 1
                return state.current_interval, True
            return state.current_interval, False

        # 2. Compute payload fingerprint (detect provider cache / identical response)
        payload_hash = self._compute_payload_hash(payload)
        is_duplicate = (payload_hash is not None and payload_hash == state.last_payload_hash)
        state.last_payload_hash = payload_hash

        metric = self._extract_metric(payload)

        new_interval = state.current_interval

        # Case A: Identical payload -> Provider hasn't recalculated data.
        # Back off smoothly towards max_interval_s.
        if is_duplicate:
            new_interval = min(self.max_interval_s, state.current_interval + self.step_up_s)
            state.stable_cycles += 1
            reason = f"duplicate payload (hash match), stepped up by +{self.step_up_s:.0f}s"

        # Case B: Payload changed, analyze numerical dynamics
        elif metric is not None:
            if state.last_metric_value is not None:
                denom = max(abs(state.last_metric_value), 1.0)
                delta_ratio = abs(metric - state.last_metric_value) / denom

                if delta_ratio >= self.volatility_threshold:
                    # High volatility / sudden shift -> immediate contraction to min_interval
                    new_interval = self.min_interval_s
                    state.volatile_cycles += 1
                    reason = f"high volatility (|Δ|={delta_ratio:.1%}), contracted to min {self.min_interval_s:.0f}s"
                elif delta_ratio <= self.stable_threshold:
                    # Stable traffic -> increase interval towards max_interval_s
                    new_interval = min(self.max_interval_s, state.current_interval + self.step_up_s)
                    state.stable_cycles += 1
                    reason = f"calm traffic (|Δ|={delta_ratio:.1%}), stepped up by +{self.step_up_s:.0f}s"
                else:
                    # Moderate change -> hold or slightly reduce towards balanced midpoint
                    if state.current_interval > 120.0:
                        new_interval = max(self.min_interval_s, state.current_interval - self.step_up_s)
                        reason = f"moderate dynamic (|Δ|={delta_ratio:.1%}), eased down"
                    else:
                        new_interval = state.current_interval
                        reason = "moderate dynamic, maintained"
            else:
                # First metric observation: start at min_interval_s or maintain
                new_interval = state.current_interval
                reason = "initial metric baseline established"

            state.last_metric_value = metric

        else:
            # Non-numerical payload that changed: gentle backoff or retain
            new_interval = min(self.max_interval_s, state.current_interval + self.step_up_s)
            reason = "non-numerical payload changed, stepped up"

        # Enforce strict bounds
        new_interval = round(max(self.min_interval_s, min(self.max_interval_s, new_interval)), 1)
        has_changed = (new_interval != prev_interval)

        if has_changed:
            state.adjustment_count += 1
            logger.info(
                f"⏱️ [AdaptivePoller] '{source_id}': {prev_interval:.0f}s -> {new_interval:.0f}s ({reason})"
            )

        state.current_interval = new_interval
        return new_interval, has_changed

    def _compute_payload_hash(self, payload: Any) -> Optional[str]:
        """Computes MD5 hash representation of raw or structured payload."""
        if payload is None:
            return None
        try:
            if isinstance(payload, (dict, list)):
                encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            elif isinstance(payload, bytes):
                encoded = payload
            else:
                encoded = str(payload).encode("utf-8")
            return hashlib.md5(encoded).hexdigest()
        except Exception:
            return None

    def _extract_metric(self, payload: Any) -> Optional[float]:
        """
        Recursively extracts the primary scalar traffic metric (e.g., speed, flow).
        Supports TomTom (flowSegmentData), Waze, and flat JSON payloads.
        """
        if isinstance(payload, (int, float)):
            return float(payload)

        if isinstance(payload, str):
            # Check if payload is a serialized JSON string
            try:
                parsed = json.loads(payload)
                return self._extract_metric(parsed)
            except Exception:
                return None

        if isinstance(payload, dict):
            # 1. Specialized TomTom flowSegmentData nesting
            if "flowSegmentData" in payload and isinstance(payload["flowSegmentData"], dict):
                flow_data = payload["flowSegmentData"]
                for k in ["currentSpeed", "freeFlowSpeed", "currentTravelTime"]:
                    if k in flow_data and isinstance(flow_data[k], (int, float)):
                        return float(flow_data[k])

            # 2. Case-insensitive search for traffic metric keys
            lowered = {str(k).lower(): v for k, v in payload.items()}
            for key in self.METRIC_KEYWORDS:
                if key in lowered:
                    val = lowered[key]
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        try:
                            return float(val)
                        except ValueError:
                            pass

            # 3. Recursive inspection for nested dicts (up to 2 levels)
            for v in payload.values():
                if isinstance(v, dict):
                    res = self._extract_metric(v)
                    if res is not None:
                        return res
                elif isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    res = self._extract_metric(v[0])
                    if res is not None:
                        return res

        elif isinstance(payload, list) and len(payload) > 0:
            return self._extract_metric(payload[0])

        return None
