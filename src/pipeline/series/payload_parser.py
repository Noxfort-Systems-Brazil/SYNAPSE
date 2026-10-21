# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/pipeline/series/payload_parser.py
# Description: Schema-aware heterogeneous sensor payload item parser (SOLID: SRP).

from typing import Any, Dict, List, Optional, Set
import numpy as np


class SeriesPayloadParser:
    """
    Parses heterogeneous sensor payload items into scalar float measurements.
    Supports O(1) compiled fast-path as well as schema-discovering recursive fallback.
    """

    @classmethod
    def parse_item(
        cls,
        item: Any,
        recipe: Optional[Dict[str, Any]],
        traffic_keys: List[str],
        detection_list_keys: List[str],
        ignore_keys: Set[str],
        to_si: bool = False,
    ) -> float:
        """Parses a single item into a float measurement with recursive schema resolution."""
        # Fast-path: O(1) compiled recipe evaluation
        if recipe is not None and recipe.get("mode") != "fallback":
            mode = recipe["mode"]
            path = recipe["field_path"]
            factor = recipe["si_factor"] if to_si else 1.0

            if mode == "detection_list":
                if isinstance(item, dict) and path[0] in item:
                    val = item[path[0]]
                    if isinstance(val, (list, tuple)):
                        return float(len(val)) * factor
            elif mode == "direct_key":
                if isinstance(item, dict) and path[0] in item:
                    res = cls.extract_value(item[path[0]])
                    if res is not None:
                        return res * factor
            elif mode == "nested_key":
                if isinstance(item, dict) and path[0] in item and isinstance(item[path[0]], dict):
                    sub = item[path[0]]
                    if len(path) > 1 and path[1] in sub:
                        res = cls.extract_value(sub[path[1]])
                        if res is not None:
                            return res * factor
            elif mode == "csv_row":
                csv_str = item[0] if (isinstance(item, (list, tuple)) and len(item) > 0) else (item if isinstance(item, str) else None)
                if csv_str and isinstance(csv_str, str) and "," in csv_str:
                    mod = recipe.get("modality", "")
                    if "speed" in mod.lower():
                        parts = [p.strip() for p in csv_str.split(",")]
                        col_idx = path[0] if (path and len(path) > 0 and isinstance(path[0], int)) else 7
                        if len(parts) > col_idx:
                            try:
                                return float(parts[col_idx]) * factor
                            except ValueError:
                                pass
                    return float(len(item)) if isinstance(item, (list, tuple)) else 1.0

        if isinstance(item, (int, float)):
            factor = recipe["si_factor"] if (recipe and to_si) else 1.0
            return float(item) * factor

        if isinstance(item, dict):
            # 1. Check for Computer Vision detection lists or event lists
            for det_k in detection_list_keys:
                if det_k in item and isinstance(item[det_k], (list, tuple)):
                    det_list = item[det_k]
                    if len(det_list) > 0 and isinstance(det_list[0], dict):
                        speeds = []
                        for d in det_list:
                            if not isinstance(d, dict):
                                continue
                            s = d.get("speed", d.get("speedKMH", d.get("speed_kmh")))
                            if s is None and "attributes" in d and isinstance(d["attributes"], dict):
                                s = d["attributes"].get("estimated_speed_kmh", d["attributes"].get("speed"))
                            if s is not None:
                                try:
                                    speeds.append(float(s))
                                except (ValueError, TypeError):
                                    pass
                        if speeds:
                            return float(np.mean(speeds))
                    return float(len(det_list))

            # 2. Check prioritized primary traffic keys (case-insensitive)
            item_lower = {str(k).lower(): (k, v) for k, v in item.items()}
            for target_k in traffic_keys:
                target_lower = target_k.lower()
                if target_lower in item_lower:
                    _, v = item_lower[target_lower]
                    res = cls.extract_value(v)
                    if res is not None:
                        return res

            # 3. Check for nested dictionary structures (e.g. TomTom flowSegmentData)
            for k, v in item.items():
                if str(k).lower() in ignore_keys:
                    continue
                if isinstance(v, dict):
                    nested_res = cls.parse_item(
                        v,
                        recipe=recipe,
                        traffic_keys=traffic_keys,
                        detection_list_keys=detection_list_keys,
                        ignore_keys=ignore_keys,
                        to_si=to_si,
                    )
                    if nested_res != 0.0:
                        return nested_res

            # 4. Fallback: Scan dict values ignoring metadata/IDs
            for k, v in item.items():
                if str(k).lower() in ignore_keys:
                    continue
                res = cls.extract_value(v)
                if res is not None:
                    return res

            return 0.0

        if isinstance(item, (list, tuple)):
            if len(item) == 0:
                return 0.0
            if isinstance(item[0], dict):
                return float(len(item))
            if isinstance(item[0], (int, float)):
                return float(item[0])
            if isinstance(item[0], str):
                try:
                    return float(item[0])
                except ValueError:
                    if "," in item[0]:
                        parts = [p.strip() for p in item[0].split(",")]
                        factor = recipe["si_factor"] if (recipe and to_si) else 1.0
                        mod = (recipe.get("modality") if recipe else "") or ""
                        if "speed" in mod.lower() and len(parts) >= 8:
                            try:
                                return float(parts[7]) * (factor if to_si else 1.0)
                            except (ValueError, IndexError):
                                pass
                        return float(len(item))
                    return 0.0
            return float(len(item))

        if isinstance(item, str):
            try:
                return float(item)
            except ValueError:
                if "," in item:
                    parts = [p.strip() for p in item.split(",")]
                    mod = (recipe.get("modality") if recipe else "") or ""
                    factor = recipe["si_factor"] if (recipe and to_si) else 1.0
                    if "speed" in mod.lower() and len(parts) >= 8:
                        try:
                            return float(parts[7]) * (factor if to_si else 1.0)
                        except (ValueError, IndexError):
                            pass
                    return 1.0
                return 0.0

        return 0.0

    @staticmethod
    def extract_value(val: Any) -> Optional[float]:
        """Safely extracts a numeric float from scalar or string value."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            try:
                if len(val) > 20 or ("-" in val and len(val) > 10):
                    if "," in val:
                        parts = [p.strip() for p in val.split(",")]
                        if len(parts) >= 8:
                            try:
                                return float(parts[7])
                            except (ValueError, IndexError):
                                pass
                    return None
                return float(val)
            except ValueError:
                if "," in val:
                    parts = [p.strip() for p in val.split(",")]
                    if len(parts) >= 8:
                        try:
                            return float(parts[7])
                        except (ValueError, IndexError):
                            pass
                return None
        if isinstance(val, (list, tuple)):
            return float(len(val))
        return None
