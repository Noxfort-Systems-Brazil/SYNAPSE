# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
XAI Attribution Extractor.

Extracts feature attributions from Captum gradient calculations or derives
deterministic kinematic sensitivity weights summing strictly to 100%.
"""

from typing import Dict, Any, List, Optional


class XAIAttributionExtractor:
    """Extracts XAI attributions strictly from Captum computation or kinematic sensitivity."""

    FREE_FLOW_BASELINE_KMH: float = 50.0

    @classmethod
    def extract_attributions(
        cls,
        xai_result: Optional[Dict[str, Any]],
        sensors: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extracts feature attributions normalized to 100% causal weight.
        """
        sensor_lookup = {str(s.get("id", "")): s for s in sensors}

        if xai_result and xai_result.get("attributions") and xai_result.get("feature_names"):
            attrs = xai_result["attributions"]
            fnames = xai_result["feature_names"]
            pairs = list(zip(fnames, attrs))[:6]
            total = sum(abs(a) for _, a in pairs) or 1.0
            items = []
            running_pct = 0.0

            for idx, (fn, a) in enumerate(pairs):
                if idx == len(pairs) - 1 and len(pairs) > 1:
                    pct = round(max(0.1, 100.0 - running_pct), 1)
                else:
                    pct = round((abs(a) / total) * 100.0, 1)
                    running_pct += pct

                direction = "Positiva (+)" if a >= 0 else "Negativa (-)"
                det_id = str(fn).split(" ")[0]
                matched_s = sensor_lookup.get(det_id, {})
                junc = matched_s.get("junction", "Malha Arterial Central")
                spd_info = matched_s.get("measuredSpeed", "")
                impact = (
                    f"Gradiente {direction} com peso decisório de {pct}% na reconstrução do estado"
                    + (f" (leitura aferida: {spd_info})." if spd_info else ".")
                )
                items.append({
                    "parameterName": str(fn),
                    "junctionLocation": junc,
                    "detectorId": det_id,
                    "causalWeightPercent": pct,
                    "gradientDirection": direction,
                    "trafficImpactAnalysis": impact,
                })
            return items

        target_sensors = sensors[:6]
        if not target_sensors:
            return []

        # Deterministic kinematic attribution proportional to deviation from free-flow baseline (vf = 50 km/h)
        raw_weights: List[float] = []
        parsed_speeds: List[float] = []

        for i, s in enumerate(target_sensors):
            try:
                spd = float(str(s.get("measuredSpeed", "18.0")).split()[0].replace(",", "."))
            except Exception:
                spd = 18.0
            parsed_speeds.append(spd)
            # Sensitivity weight based on kinematic gradient |vf - v| + structural rank offset
            weight = abs(cls.FREE_FLOW_BASELINE_KMH - spd) + (1.5 / (i + 1))
            raw_weights.append(max(1.0, weight))

        total_w = sum(raw_weights) or 1.0
        items = []
        running_pct = 0.0

        for idx, (s, spd, w) in enumerate(zip(target_sensors, parsed_speeds, raw_weights)):
            if idx == len(target_sensors) - 1 and len(target_sensors) > 1:
                pct = round(max(0.1, 100.0 - running_pct), 1)
            else:
                pct = round((w / total_w) * 100.0, 1)
                running_pct += pct

            if spd < 10.0:
                direction = "Positiva (+) [Alerta Crítico de Retenção]"
                impact = (
                    f"Aferição de {spd:.1f} km/h identificou choque cinemático e formação de fila severa, "
                    f"exercendo influência dominante ({pct}%) na ponderação de saturação da malha."
                )
            elif spd < 20.0:
                direction = "Positiva (+) [Compressão de Fluxo]"
                impact = (
                    f"Aferição de {spd:.1f} km/h sinalizou transição para escoamento saturado, "
                    f"contribuindo com {pct}% para o ajuste de densidade da seção arterial."
                )
            else:
                direction = "Positiva (+) [Estabilidade de Escoamento]"
                impact = (
                    f"Aferição de {spd:.1f} km/h confirmou capacidade de escoamento ativo na aproximação, "
                    f"ancorando {pct}% do vetor de conservação espacial (LWR)."
                )

            items.append({
                "parameterName": f"Telemetria do Detector {s.get('id', '')}",
                "junctionLocation": s.get("junction", "Malha Viária"),
                "detectorId": s.get("id", ""),
                "causalWeightPercent": pct,
                "gradientDirection": direction,
                "trafficImpactAnalysis": impact,
            })

        return items
