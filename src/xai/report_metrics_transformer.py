# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List


class ReportMetricsTransformer:
    """
    Transforms, normalizes, and ranks neural feature attributions and sensor metrics
    for consumption by official report block renderers.
    Guarantees strict compliance with the Completeness Axiom (100% total weight).
    """

    @staticmethod
    def transform_agent_metrics(analyses: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Calculates normalized percentages (summing to 100%), extracts top contributors
        and formats ABNT strings per station/detector.
        """
        transformed: Dict[str, Dict[str, Any]] = {}

        for aid, res in analyses.items():
            sorted_analysis = res.get("sorted_analysis", []) if isinstance(res, dict) else []
            has_data = bool(res and sorted_analysis)

            if not has_data:
                transformed[aid] = {
                    "has_data": False,
                    "items": [],
                    "top_3": [],
                    "image_base64": res.get("image_base64") if isinstance(res, dict) else None,
                }
                continue

            total_imp = sum(abs(float(item.get("importance", 0.0))) for item in sorted_analysis) or 1.0

            from src.formatters.report_number_formatter import ReportNumberFormatter

            items: List[Dict[str, Any]] = []
            for item in sorted_analysis:
                name = item.get("name", "Sensor")
                imp = abs(float(item.get("importance", 0.0)))
                desc = item.get("description", "")
                pct = (imp / total_imp) * 100.0
                pct_str = ReportNumberFormatter.format_percent(pct, decimal_places=1)

                items.append({
                    "name": name,
                    "importance": imp,
                    "pct": pct,
                    "pct_str": pct_str,
                    "description": desc,
                })

            top_3 = sorted(items, key=lambda x: x["importance"], reverse=True)[:3]

            transformed[aid] = {
                "has_data": True,
                "items": items,
                "top_3": top_3,
                "image_base64": res.get("image_base64"),
            }

        return transformed
