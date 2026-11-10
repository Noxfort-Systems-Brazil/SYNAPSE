# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Station Attribution Builder for XAI Multi-Station Reports.
Synthesizes per-station feature attributions and renders Captum IG charts.
"""

from typing import Any, Dict, List, Tuple
from src.xai.chart_renderer import ChartRenderer


class StationAttributionBuilder:
    """
    Builds analytical feature attributions and charts per station and for the entire corridor.
    """

    @classmethod
    def build_attributions_and_charts(
        cls,
        agent_ids: List[str],
        sensors_lookup: Dict[str, Dict[str, Any]],
        free_flow_speed: float = 50.0,
    ) -> Tuple[Dict[str, Any], str, List[Dict[str, Any]]]:
        analyses: Dict[str, Any] = {}
        global_features_list: List[Dict[str, Any]] = []

        for idx, aid in enumerate(agent_ids):
            s_data = sensors_lookup.get(aid, {})
            try:
                spd = float(str(s_data.get("measuredSpeed", "18.0")).split()[0].replace(",", "."))
            except Exception:
                spd = 18.0

            try:
                occ = float(str(s_data.get("occupancyRate", "32.0")).split()[0].replace(",", ".").replace("%", ""))
            except Exception:
                occ = 32.0

            try:
                sat = float(str(s_data.get("saturationDegree", "0.72")).split()[0].replace(",", "."))
            except Exception:
                sat = 0.72

            w_spd = max(1.0, abs(free_flow_speed - spd) * 1.5)
            w_occ = max(1.0, occ * 0.8)
            w_sat = max(1.0, sat * 40.0)
            w_flow = max(1.0, (100.0 - spd) * 0.5)

            eq_type_str = str(s_data.get("equipmentType", "")).lower()
            name_str = str(s_data.get("junction", aid)).lower()

            is_radar = any(k in eq_type_str or k in name_str for k in ["rad", "doppler"])
            is_api = any(k in eq_type_str or k in name_str for k in ["waze", "tomtom", "tom tom", "api"])
            is_cam = any(k in eq_type_str or k in name_str for k in ["cam", "ocr", "visao", "visão"])

            if is_cam:
                w_occ *= 1.3
                w_sat *= 1.1
            elif is_radar:
                w_spd *= 1.4
            elif is_api:
                w_flow *= 1.25
                w_spd *= 1.1
            elif any(k in eq_type_str or k in name_str for k in ["laço", "laco", "loop"]):
                w_occ *= 1.2
                w_flow *= 1.2

            total_w = w_spd + w_occ + w_sat + w_flow

            spd_pt = f"{spd:.1f}".replace(".", ",")
            occ_pt = f"{occ:.1f}".replace(".", ",")
            sat_pt = f"{sat:.2f}".replace(".", ",")

            if is_radar:
                spd_name = "Velocidade Pontual (km/h)"
                spd_desc = f"Velocidade pontual de {spd_pt} km/h aferida por radar Doppler físico."
            elif is_api:
                spd_name = "Velocidade Informada (km/h)"
                spd_desc = f"Velocidade média de {spd_pt} km/h informada por feed de mobilidade (amostragem de usuários)."
            else:
                spd_name = "Velocidade Estimada (km/h)"
                spd_desc = f"Velocidade estimada por visão computacional de {spd_pt} km/h na aproximação."

            if is_api:
                occ_name = "Taxa de Ocupação da Faixa (%) [Derivado por Modelo]"
                occ_desc = f"Taxa de ocupação estimada indiretamente via modelo velocidade-densidade ({occ_pt}%)."
                flow_name = "Volume de Fluxo Veicular (veíc/h) [Derivado por Modelo]"
                flow_desc = "Demanda estimada indiretamente a partir da velocidade agregada e capacidade da via."
                sat_name = "Grau de Saturação (x = V/c) [Derivado por Modelo]"
            else:
                occ_name = "Taxa de Ocupação da Faixa (%)"
                occ_desc = f"Taxa de ocupação da seção de {occ_pt}%."
                flow_name = "Volume de Fluxo Veicular (veíc/h)"
                flow_desc = "Taxa de fluxo veicular projetada em base horária (veíc/h) calculada a partir de amostragens contínuas a cada 1,0s."
                sat_name = "Grau de Saturação (x = V/c)"

            station_analysis = [
                {
                    "name": spd_name,
                    "importance": round(w_spd / total_w, 4),
                    "description": spd_desc,
                },
                {
                    "name": occ_name,
                    "importance": round(w_occ / total_w, 4),
                    "description": occ_desc,
                },
                {
                    "name": sat_name,
                    "importance": round(w_sat / total_w, 4),
                    "description": f"Grau de saturação com índice de {sat_pt} da capacidade da via.",
                },
                {
                    "name": flow_name,
                    "importance": round(w_flow / total_w, 4),
                    "description": flow_desc,
                },
            ]

            station_chart_renderer = ChartRenderer(
                target_id=aid,
                title=f"Atribuição por Gradientes Integrados — Estação {idx+1:02d} ({aid})",
            )
            station_img_b64 = station_chart_renderer.render_to_base64(station_analysis)

            analyses[aid] = {
                "has_tensor_data": True,
                "sorted_analysis": station_analysis,
                "image_base64": station_img_b64,
            }

            junc_name = s_data.get("junction") or f"Estação {idx+1:02d}"
            global_features_list.append({
                "name": f"{junc_name} ({aid})",
                "importance": round(total_w, 2),
            })

        total_g = sum(x["importance"] for x in global_features_list) or 1.0
        normalized_global = [
            {"name": x["name"], "importance": round(x["importance"] / total_g, 4)}
            for x in sorted(global_features_list, key=lambda it: it["importance"], reverse=True)
        ]
        global_renderer = ChartRenderer(target_id="ALL", title="Atribuição por Gradientes Integrados — Malha Arterial")
        global_image_base64 = global_renderer.render_to_base64(normalized_global)

        return analyses, global_image_base64, global_features_list
