# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Corridor Recommendation Builder for XAI Multi-Station Reports.
Synthesizes action recommendations, sensing modality phrases, and legal framing.
"""

from typing import Any, Dict, List, Optional
from src.report.traffic_regime_classifier import TrafficRegimeClassifier


class CorridorRecommendationBuilder:
    """
    Synthesizes corridor classification, action recommendations, and legal reference filters.
    """

    @classmethod
    def build(
        cls,
        sensors: List[Dict[str, Any]],
        sensors_lookup: Dict[str, Dict[str, Any]],
        report_data: Dict[str, Any],
        templates: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        corridor_info = TrafficRegimeClassifier.classify_corridor(sensors)
        mean_speed = corridor_info["average_speed"]
        network_speed = f"{mean_speed:.1f}".replace(".", ",") + " km/h"
        network_saturation = f"{corridor_info['average_saturation']:.2f}".replace(".", ",")
        network_regime = f"{corridor_info['corridor_regime']} ({corridor_info['corridor_los'].split(' (')[0]})"

        total_st = corridor_info.get("total_stations", len(sensors))
        crit_count = corridor_info.get("critical_count", 0)
        critical_stations = corridor_info.get("critical_stations", [])

        # Format network regime with explicit critical count to avoid masking retention by averaging
        regime_base = f"{corridor_info['corridor_regime']} ({corridor_info['corridor_los'].split(' (')[0]})"
        if crit_count > 0:
            network_regime = f"{regime_base}, com {crit_count} de {total_st} pontos em regime crítico"
        else:
            network_regime = f"{regime_base}, com 0 de {total_st} pontos em regime crítico"

        worst_aid = corridor_info["worst_station_id"]
        worst_station_name = corridor_info["worst_station_name"]

        if crit_count > 1:
            crit_descs = []
            has_crit_physical = False
            has_crit_feed = False
            for cs in critical_stations:
                c_aid = cs["id"]
                c_name = cs["name"]
                c_spd = f"{cs['speed']:.1f}".replace(".", ",") + " km/h"
                c_sat = f"{cs['saturation']:.2f}".replace(".", ",")
                c_sdata = sensors_lookup.get(c_aid, {})
                c_type = str(c_sdata.get("equipmentType", "")).lower()
                is_feed = "feed" in c_type or "api" in c_type or "waze" in c_type or "tomtom" in c_type
                if is_feed:
                    has_crit_feed = True
                    t_lbl = "Feed"
                else:
                    has_crit_physical = True
                    t_lbl = "Radar" if ("radar" in c_type or "doppler" in c_type) else "Detector Físico"
                crit_descs.append(f"**{c_name} (`{c_aid}` • {t_lbl} - {c_spd}, saturação {c_sat})**")

            concordance_note = ""
            if has_crit_physical and has_crit_feed:
                concordance_note = " Destaca-se que o detector físico e o feed independente concordam quanto à severidade da retenção crítica."

            critical_label = f"Pontos em regime crítico ({crit_count} de {total_st})"
            critical_points_body = " e ".join(crit_descs) + f".{concordance_note}"
            critical_bullet = f"- **{critical_label}:** {critical_points_body}"
            worst_summary = critical_points_body
        elif crit_count == 1:
            cs = critical_stations[0]
            c_aid = cs["id"]
            c_name = cs["name"]
            c_spd = f"{cs['speed']:.1f}".replace(".", ",") + " km/h"
            c_sat = f"{cs['saturation']:.2f}".replace(".", ",")
            critical_label = f"Pontos em regime crítico (1 de {total_st})"
            critical_points_body = f"**{c_name}** (`{c_aid}`), a **{c_spd}**, saturação **{c_sat}**."
            critical_bullet = f"- **{critical_label}:** {critical_points_body}"
            worst_summary = critical_points_body
        else:
            worst_spd_str = f"{corridor_info['worst_station_speed']:.1f}".replace(".", ",") + " km/h"
            worst_sat_str = f"{corridor_info['worst_station_saturation']:.2f}".replace(".", ",")
            critical_label = f"Pontos em regime crítico (0 de {total_st})"
            critical_points_body = f"Nenhum ponto em regime crítico. Ponto com maior retenção: **{worst_station_name}** (`{worst_aid}`), a **{worst_spd_str}**, saturação **{worst_sat_str}**."
            critical_bullet = f"- **Ponto com Maior Retenção:** {critical_points_body}"
            worst_summary = critical_points_body

        if crit_count > 1:
            actions = []
            for cs in critical_stations:
                c_aid = cs["id"]
                c_name = cs["name"]
                c_sdata = sensors_lookup.get(c_aid, {})
                c_type = str(c_sdata.get("equipmentType", "")).lower()
                is_feed = "feed" in c_type or "api" in c_type or "waze" in c_type or "tomtom" in c_type
                if is_feed:
                    actions.append(f"verificar em campo o trecho correspondente à estação **{c_aid}** ({c_name})")
                else:
                    actions.append(f"intervir prioritariamente com ajuste semafórico na aproximação da estação **{c_aid}** ({c_name})")

            action_recommendation = (
                f"Atuar de forma integrada nos {crit_count} pontos críticos: "
                + "; ".join(actions)
                + ", mitigando a retenção severa aferida no corredor."
            )
        elif crit_count == 1:
            cs = critical_stations[0]
            c_aid = cs["id"]
            c_name = cs["name"]
            c_sdata = sensors_lookup.get(c_aid, {})
            c_type = str(c_sdata.get("equipmentType", "")).lower()
            is_feed = "feed" in c_type or "api" in c_type or "waze" in c_type or "tomtom" in c_type
            if is_feed:
                action_recommendation = f"Verificar em campo as condições de tráfego no trecho correspondente à estação **{c_aid}** ({c_name}) antes de intervenções semafóricas diretas, por se tratar de feed de terceiros."
            else:
                action_recommendation = f"Ajustar tempos semafóricos prioritariamente na aproximação da estação **{c_aid}** ({c_name}) e avaliar planos de tráfego para mitigar a retenção crítica aferida."
        elif corridor_info["corridor_tier"] == 3 or corridor_info["worst_station_tier"] == 3:
            w_sdata = sensors_lookup.get(worst_aid, {})
            w_type = str(w_sdata.get("equipmentType", "")).lower()
            is_worst_feed = "feed" in w_type or "api" in w_type or "waze" in w_type or "tomtom" in w_type
            if is_worst_feed:
                action_recommendation = f"Verificar em campo as condições de fluidez no trecho correspondente à estação **{worst_aid}** ({worst_station_name}) antes de intervenções semafóricas diretas, visto tratar-se de estimativa baseada em feeds de terceiros."
            else:
                action_recommendation = f"Monitorar formação de filas na aproximação de **{worst_aid}** ({worst_station_name}) e avaliar extensão de verde semafórico."
        else:
            action_recommendation = "Fluxo operando dentro dos parâmetros nominais. Manter monitoramento contínuo."

        source_bullets = []
        has_radars = any("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower() for s in sensors)
        has_loops = any("laço" in str(s.get("equipmentType", "")).lower() or "laco" in str(s.get("equipmentType", "")).lower() or "loop" in str(s.get("equipmentType", "")).lower() for s in sensors)
        has_cameras = any("câmera" in str(s.get("equipmentType", "")).lower() or "camera" in str(s.get("equipmentType", "")).lower() or "ocr" in str(s.get("equipmentType", "")).lower() for s in sensors)
        has_feeds = any("feed" in str(s.get("equipmentType", "")).lower() or "api" in str(s.get("equipmentType", "")).lower() or "waze" in str(s.get("equipmentType", "")).lower() or "tomtom" in str(s.get("equipmentType", "")).lower() for s in sensors)

        if has_radars and has_loops:
            source_bullets.append("- **Detectores Físicos (Radares Doppler e Laços Indutivos):** Medições pontuais de velocidade instantânea e contagem veicular direta na pista.")
        elif has_radars:
            source_bullets.append("- **Detectores Físicos (Radares Doppler):** Medições pontuais de velocidade instantânea e contagem veicular direta na pista.")
        elif has_loops:
            source_bullets.append("- **Detectores Físicos (Laços Indutivos):** Medições de ocupação e contagem veicular direta na pista.")

        if has_cameras:
            source_bullets.append("- **Visão Computacional (Câmera):** Processamento de imagem para cálculo de densidade e ocupação visual da faixa.")
        if has_feeds:
            source_bullets.append("- **Feeds Agregados de Mobilidade (APIs de Terceiros - ex: Waze, TomTom):** Dados médios de tráfego baseados em crowdsourcing, úteis para contexto macroscópico mas sem vínculo metrológico direto de instrumentos de campo.")

        present_sources_desc = "\n".join(source_bullets) if source_bullets else "- **Fontes Monitoradas:** Telemetria multimodal consolidada."

        if has_feeds and not has_radars and not has_cameras and not has_loops:
            sensing_intro = "O sistema processou feeds de mobilidade urbana agregados por APIs de terceiros para compor o panorama de tráfego do corredor viário."
        elif (has_radars or has_cameras or has_loops) and not has_feeds:
            sensing_intro = "O sistema processou telemetria de detectores físicos de campo para compor a matriz de tráfego da malha arterial."
        else:
            sensing_intro = "O sistema sintetizou dados de fontes multimodais heterogêneas para compor a matriz de tráfego da malha arterial."

        has_enforcement_radar = any(
            ("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower()) and
            (bool(s.get("is_enforcement")) or "fiscaliz" in str(s.get("purpose", "")).lower() or "autua" in str(s.get("purpose", "")).lower() or "fiscaliz" in str(s.get("equipmentType", "")).lower())
            for s in sensors
        )
        if not has_enforcement_radar:
            report_data["references"] = [r for r in report_data.get("references", []) if "798" not in str(r)]
            report_data["legalFraming"] = [lf for lf in report_data.get("legalFraming", []) if "798" not in str(lf.get("article", ""))]

        has_personal_data = any(
            "placa" in str(s.get("equipmentType", "")).lower() or
            "lpr" in str(s.get("equipmentType", "")).lower() or
            "reconhecimento de placa" in str(s.get("equipmentType", "")).lower() or
            bool(s.get("processes_personal_data"))
            for s in sensors
        )
        if not has_personal_data:
            report_data["references"] = [r for r in report_data.get("references", []) if "13.709" not in str(r) and "LGPD" not in str(r)]
            report_data["legalFraming"] = [lf for lf in report_data.get("legalFraming", []) if "13.709" not in str(lf.get("article", "")) and "LGPD" not in str(lf.get("article", ""))]

        return {
            "network_speed": network_speed,
            "network_saturation": network_saturation,
            "network_regime": network_regime,
            "worst_summary": worst_summary,
            "critical_bullet": critical_bullet,
            "critical_label": critical_label,
            "worst_aid": worst_aid,
            "worst_station_name": worst_station_name,
            "action_recommendation": action_recommendation,
            "present_source_types_description": present_sources_desc,
            "sensing_intro_phrase": sensing_intro,
            "report_data": report_data,
        }
