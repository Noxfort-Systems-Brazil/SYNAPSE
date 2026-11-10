# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List, Optional, Set, Tuple


class SeriesRecipeCompiler:
    """
    Compiles O(1) data access recipes and International System (SI) conversion
    parameters from heterogeneous sensor sample packets.
    """

    @staticmethod
    def get_si_conversion_factor(unit: Optional[str], modality: Optional[str] = None) -> Tuple[float, str]:
        """Returns the multiplicative factor to convert raw unit to International System (SI)."""
        if not unit:
            return 1.0, "unit"
        u = unit.strip().lower()
        if u in ("km/h", "kmh"):
            return 1.0 / 3.6, "m/s"
        if u == "mph":
            return 1.0 / 2.23694, "m/s"
        if u in ("veh/h", "veic/h", "vph"):
            return 1.0 / 3600.0, "veh/s"
        if u in ("veh/min", "veic/min", "vpm"):
            return 1.0 / 60.0, "veh/s"
        if u in ("veh/km", "veic/km"):
            return 1.0 / 1000.0, "veh/m"
        return 1.0, unit

    @classmethod
    def compile_recipe(
        cls,
        sample_chunk: List[Any],
        traffic_keys: List[str],
        detection_list_keys: List[str],
        ignore_keys: Set[str],
        modality: Optional[str] = None,
        unit: Optional[str] = None,
        to_si: bool = True,
    ) -> Dict[str, Any]:
        """
        Discovers the optimal O(1) extraction recipe from sample packets.
        Compiles the direct access path, parsing mode, and SI conversion factor.
        """
        factor, si_unit = cls.get_si_conversion_factor(unit, modality)

        recipe: Dict[str, Any] = {
            "mode": "fallback",
            "field_path": [],
            "raw_unit": unit or "unit",
            "si_unit": si_unit,
            "si_factor": factor,
            "modality": modality or "unknown",
        }

        if not sample_chunk:
            return recipe

        first_sample = sample_chunk[0]

        if isinstance(first_sample, dict):
            # 1. Detection list mode (Computer Vision cameras)
            for det_k in detection_list_keys:
                if det_k in first_sample and isinstance(first_sample[det_k], (list, tuple)):
                    recipe["mode"] = "detection_list"
                    recipe["field_path"] = [det_k]
                    return recipe

            # 2. Direct key in top-level dict
            item_lower = {str(k).lower(): k for k in first_sample.keys()}
            for target_k in traffic_keys:
                target_lower = target_k.lower()
                if target_lower in item_lower:
                    orig_k = item_lower[target_lower]
                    recipe["mode"] = "direct_key"
                    recipe["field_path"] = [orig_k]
                    return recipe

            # 3. Nested dict (e.g. TomTom flowSegmentData)
            for k, v in first_sample.items():
                if str(k).lower() in ignore_keys:
                    continue
                if isinstance(v, dict):
                    nested_lower = {str(nk).lower(): nk for nk in v.keys()}
                    for target_k in traffic_keys:
                        if target_k.lower() in nested_lower:
                            recipe["mode"] = "nested_key"
                            recipe["field_path"] = [k, nested_lower[target_k.lower()]]
                            return recipe

        # 4. CSV string or list of CSV strings mode (Inductive loops / passage telemetry)
        csv_str = None
        if isinstance(first_sample, (list, tuple)) and len(first_sample) > 0 and isinstance(first_sample[0], str) and "," in first_sample[0]:
            csv_str = first_sample[0]
        elif isinstance(first_sample, str) and "," in first_sample:
            csv_str = first_sample

        if csv_str is not None:
            recipe["mode"] = "csv_row"
            recipe["field_path"] = [7]  # Column 7 = SPEED_KMH in loop template
            return recipe

        return recipe
