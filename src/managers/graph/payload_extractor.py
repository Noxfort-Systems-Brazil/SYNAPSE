# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass

from src.physics.constants import SpeedConverter


@dataclass
class ExtractedTelemetry:
    value: float
    is_speed_sensor: bool
    is_flow_sensor: bool
    is_count_sensor: bool
    measured_speed_ms: Optional[float] = None


class TelemetryPayloadExtractor:
    """Parses heterogeneous sensor telemetry into normalized numeric invariants."""

    @staticmethod
    def parse_value(payload: Any) -> float:
        """Extracts normalized scalar value in SI units."""
        try:
            if isinstance(payload, (int, float)):
                return float(payload)
            if isinstance(payload, list) and len(payload) > 0:
                if isinstance(payload[0], (int, float)):
                    return float(payload[0])
                if isinstance(payload[0], dict):
                    return float(len(payload))
                if isinstance(payload[0], str):
                    try:
                        return float(payload[0])
                    except ValueError:
                        if "," in payload[0]:
                            parts = [p.strip() for p in payload[0].split(",")]
                            if len(parts) >= 8:
                                try:
                                    return SpeedConverter.to_ms(float(parts[7]), "km/h")
                                except (ValueError, IndexError):
                                    pass
                            return float(len(payload))
            if isinstance(payload, str):
                try:
                    return float(payload)
                except ValueError:
                    if "," in payload:
                        parts = [p.strip() for p in payload.split(",")]
                        if len(parts) >= 8:
                            try:
                                return SpeedConverter.to_ms(float(parts[7]), "km/h")
                            except (ValueError, IndexError):
                                pass
                        return 1.0
            if isinstance(payload, dict):
                if "value" in payload and isinstance(payload["value"], (int, float)):
                    return float(payload["value"])
                if "speed_kmh" in payload:
                    return SpeedConverter.to_ms(float(payload["speed_kmh"]), "km/h")
                if "speed" in payload:
                    s = float(payload["speed"])
                    return s if s <= 35.0 else SpeedConverter.to_ms(s, "km/h")
                if "flow" in payload:
                    return float(payload["flow"])
        except Exception:
            return 0.0
        return 0.0

    @classmethod
    def extract(
        cls,
        source_id: str,
        payload: Any,
        raw_payload: Any,
        semantic_type: str,
        meta: Dict[str, Any]
    ) -> ExtractedTelemetry:
        val = cls.parse_value(payload)

        source_desc = f"{source_id} {meta.get('name', '')} {meta.get('source_name', '')}".lower()

        # Check if raw_payload is or contains a CSV passage row:
        csv_row = None
        if isinstance(raw_payload, list) and len(raw_payload) > 0 and isinstance(raw_payload[0], str) and "," in raw_payload[0]:
            csv_row = raw_payload[0]
        elif isinstance(raw_payload, str) and "," in raw_payload:
            csv_row = raw_payload

        # Check if raw_payload is a list of recognition dicts (Computer Vision)
        is_rec_list = (
            isinstance(raw_payload, list)
            and len(raw_payload) > 0
            and isinstance(raw_payload[0], dict)
        )

        is_speed = (
            semantic_type == "Vehicle Speed"
            or (isinstance(raw_payload, dict) and "speed_kmh" in raw_payload)
            or (isinstance(meta.get("extraction_path"), list) and "speed_kmh" in meta.get("extraction_path"))
        )
        is_flow = (
            semantic_type == "Traffic Flow"
            or (isinstance(raw_payload, dict) and "flow" in raw_payload)
        )
        is_count = (
            semantic_type in ("Vehicle Count", "Count")
            or any(k in source_desc for k in ("cam", "camera", "loop", "laço", "detector", "count"))
            or is_rec_list
            or csv_row is not None
            or (
                isinstance(raw_payload, dict)
                and any(
                    k in raw_payload and isinstance(raw_payload[k], list)
                    for k in ("recognitions", "detections", "vehicles", "data")
                )
            )
        )

        measured_speed_ms = None
        # Case A: Dict payload
        if isinstance(raw_payload, dict):
            if "speed_kmh" in raw_payload:
                measured_speed_ms = SpeedConverter.to_ms(float(raw_payload["speed_kmh"]), "km/h")
            elif "speed" in raw_payload:
                s = float(raw_payload["speed"])
                measured_speed_ms = s if s <= 35.0 else SpeedConverter.to_ms(s, "km/h")
            else:
                for det_k in ("recognitions", "data", "detections", "vehicles"):
                    if det_k in raw_payload and isinstance(raw_payload[det_k], list):
                        spd_list = []
                        for r in raw_payload[det_k]:
                            if isinstance(r, dict):
                                spd = r.get("estimated_speed_kmh") or r.get("speed_kmh") or r.get("speed")
                                if spd is None and "vehicle" in r and isinstance(r["vehicle"], dict):
                                    veh = r["vehicle"]
                                    attr = veh.get("attributes", {})
                                    if isinstance(attr, dict):
                                        spd = attr.get("estimated_speed_kmh") or attr.get("speed")
                                    if spd is None:
                                        spd = veh.get("estimated_speed_kmh") or veh.get("speed_kmh") or veh.get("speed")
                                if spd is not None:
                                    try:
                                        spd_list.append(float(spd))
                                    except (ValueError, TypeError):
                                        pass
                        if spd_list:
                            avg_kmh = sum(spd_list) / len(spd_list)
                            measured_speed_ms = SpeedConverter.to_ms(avg_kmh, "km/h")
                            break

        # Case B: List of recognition dicts (CV camera events)
        elif is_rec_list:
            spd_list = []
            for r in raw_payload:
                if isinstance(r, dict):
                    spd = r.get("estimated_speed_kmh") or r.get("speed_kmh") or r.get("speed")
                    if spd is None and "vehicle" in r and isinstance(r["vehicle"], dict):
                        veh = r["vehicle"]
                        attr = veh.get("attributes", {})
                        if isinstance(attr, dict):
                            spd = attr.get("estimated_speed_kmh") or attr.get("speed")
                        if spd is None:
                            spd = veh.get("estimated_speed_kmh") or veh.get("speed_kmh") or veh.get("speed")
                    if spd is not None:
                        try:
                            spd_list.append(float(spd))
                        except (ValueError, TypeError):
                            pass
            if spd_list:
                avg_kmh = sum(spd_list) / len(spd_list)
                measured_speed_ms = SpeedConverter.to_ms(avg_kmh, "km/h")

        # Case C: CSV row string (Inductive loops / passage records)
        elif csv_row is not None:
            parts = [p.strip() for p in csv_row.split(",")]
            if len(parts) >= 8:
                try:
                    spd_kmh = float(parts[7])
                    measured_speed_ms = SpeedConverter.to_ms(spd_kmh, "km/h")
                except (ValueError, IndexError):
                    pass
            if val == 0.0:
                val = float(len(raw_payload)) if isinstance(raw_payload, list) else 1.0

        if is_count and val == 0.0 and (is_rec_list or csv_row is not None):
            val = float(len(raw_payload)) if isinstance(raw_payload, list) else 1.0

        return ExtractedTelemetry(
            value=val,
            is_speed_sensor=is_speed,
            is_flow_sensor=is_flow,
            is_count_sensor=is_count,
            measured_speed_ms=measured_speed_ms
        )
