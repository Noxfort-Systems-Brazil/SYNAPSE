# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Pre-Markdown Report Validation Rules (Domain Integrity Specifications).
"""

from typing import Any, Dict, List, Optional
from src.report.traffic_regime_classifier import TrafficRegimeClassifier
from src.validation.exceptions import ReportViolation
from src.validation.base_rule import PreMarkdownRule


class DataPresenceRule(PreMarkdownRule):
    """Rule 8: Ensures the report contains at least one active sensor/station."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        sensors = report_data.get("sensors", [])
        if not sensors:
            return [
                ReportViolation(
                    error_class=8,
                    title="Dados Ausentes",
                    message="A lista de sensores/estações está vazia. O relatório requer ao menos 1 estação monitorada.",
                    section="Dados de Entrada",
                )
            ]
        return []


class WorstCriteriaSeverityRule(PreMarkdownRule):
    """Rule 3: Enforces tie-breaker rule: operational status >= max(tier_speed, tier_saturation)."""

    @classmethod
    def validate_severity(cls, report_data: Dict[str, Any]) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        for s in sensors:
            op_status = s.get("operational_status")
            if not op_status:
                continue
            spd_val = TrafficRegimeClassifier._parse_numeric(s.get("measuredSpeed"), default=25.0)
            raw_sat = s.get("saturation") if s.get("saturation") is not None else s.get("saturationDegree")
            sat_val = TrafficRegimeClassifier._parse_numeric(raw_sat, default=0.65)
            tier_spd = TrafficRegimeClassifier.classify_by_speed(spd_val)
            tier_sat = TrafficRegimeClassifier.classify_by_saturation(sat_val)
            worst_tier = max(tier_spd, tier_sat)
            expected_tier_info = TrafficRegimeClassifier.TIERS[worst_tier - 1]
            expected_status = expected_tier_info.status_label

            if op_status.lower() != expected_status.lower() and op_status.split(" / ")[0].lower() not in expected_status.lower():
                declared_tier = 1
                for t in reversed(TrafficRegimeClassifier.TIERS):
                    if t.status_label.lower() in op_status.lower() or op_status.lower() in t.status_label.lower():
                        declared_tier = t.tier
                        break
                    if t.name.lower() in op_status.lower():
                        declared_tier = t.tier
                        break
                if declared_tier < worst_tier:
                    violations.append(
                        ReportViolation(
                            error_class=3,
                            title="Status Abaixo da Severidade do Pior Critério",
                            message=(
                                f"Estação '{s.get('id', '')}' declarou status '{op_status}' (Nível {declared_tier}), "
                                f"mas o pior critério (Velocidade Nível {tier_spd}, Saturação Nível {tier_sat}) "
                                f"exige Nível {worst_tier} ('{expected_status}')."
                            ),
                            section="Quadro Sintético (1.3)",
                        )
                    )
                else:
                    violations.append(
                        ReportViolation(
                            error_class=3,
                            title="Contradição de Status Operacional",
                            message=f"Estação {s.get('id', '')} declarou status '{op_status}', mas sua telemetria ({spd_val:.1f} km/h, saturação {sat_val:.2f}) classifica-se como '{expected_status}'.",
                            section="Quadro Sintético (1.3)",
                        )
                    )
        return violations

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        return self.validate_severity(report_data)


class SourceTypologyPreRule(PreMarkdownRule):
    """Rule 4: Validates source typology consistency in raw telemetry structures."""

    @classmethod
    def validate_pre_typology(cls, report_data: Dict[str, Any]) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])

        for s in sensors:
            sid = str(s.get("id", ""))
            eq_type = str(s.get("equipmentType", "")).lower()
            is_feed = s.get("canonical_source_type") == "third_party_feed" or (
                s.get("canonical_source_type") is None
                and any(t in eq_type for t in ["feed de terceiros", "waze", "tomtom", "crowdsourcing"])
            )
            spd_label = str(s.get("speedLabel", "")).lower()
            spd_raw = str(s.get("measuredSpeed", "")).lower()

            if ("radar" in eq_type or "doppler" in eq_type) and "feed" in eq_type:
                violations.append(
                    ReportViolation(
                        error_class=4,
                        title="Tipologia Conflitante",
                        message=f"Sensor {sid} rotulado simultaneamente como radar físico e feed: '{s.get('equipmentType')}'.",
                        section="Classificação de Fontes",
                    )
                )

            if is_feed:
                if "aferida" in spd_label or "aferida" in spd_raw:
                    violations.append(
                        ReportViolation(
                            error_class=4,
                            title="Vocabulário Incompatível com Tipologia de Fonte",
                            message=f"Fonte feed '{sid}' utiliza termo 'aferida', reservado a instrumentos com vínculo metrológico.",
                            section="Classificação de Fontes",
                        )
                    )
                for forbidden in ["radar físico", "radar fisico", "laço", "detector de campo"]:
                    if forbidden in eq_type:
                        violations.append(
                            ReportViolation(
                                error_class=4,
                                title="Tipologia Conflitante",
                                message=f"Sensor feed '{sid}' possui referência física proibida: '{forbidden}'.",
                                section="Classificação de Fontes",
                            )
                        )
        return violations

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        return self.validate_pre_typology(report_data)


class StationNarrativePreRule(PreMarkdownRule):
    """Rule 2: Validates that station narrative cites top-2 weighted features."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        for s in sensors:
            nar = s.get("station_narrative")
            weights = s.get("xai_weights")
            if nar and isinstance(weights, dict):
                sorted_f = sorted(weights.items(), key=lambda kv: float(kv[1]), reverse=True)
                top2_names = [k.lower() for k, _ in sorted_f[:2]]
                nar_lower = nar.lower()
                matched = sum(1 for name in top2_names if name in nar_lower)
                if matched < 2:
                    violations.append(
                        ReportViolation(
                            error_class=2,
                            title="Síntese Desalinhada com Pesos",
                            message=f"A síntese da estação '{s.get('id')}' não cita adequadamente as 2 variáveis de maior peso ({', '.join(top2_names)}).",
                            section="Fichas de Explicabilidade (Anexo I)",
                        )
                    )
        return violations


class RecommendationConfidenceRule(PreMarkdownRule):
    """Rule 5: Validates recommendation attenuation for non-metrological sources."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        ctx = context or {}
        sensors = report_data.get("sensors", [])
        action_rec = str(ctx.get("action_recommendation") or report_data.get("action_recommendation", ""))
        corridor_info = TrafficRegimeClassifier.classify_corridor(sensors)
        worst_id = corridor_info.get("worst_station_id", "")
        worst_sensor = next((s for s in sensors if (s.get("id") == worst_id or s.get("junction") == worst_id)), None)

        if worst_sensor:
            w_type = str(worst_sensor.get("equipmentType", "")).lower()
            if ("feed" in w_type or "api" in w_type) and action_rec:
                if not any(token in action_rec.lower() for token in ["verificar em campo", "verificação in loco", "avaliar", "confirmado"]):
                    violations.append(
                        ReportViolation(
                            error_class=5,
                            title="Recomendação Excessiva em Fonte Não-Metrológica",
                            message=f"A estação mais retida ({worst_id}) baseia-se em feed de terceiros. A recomendação deve ser atenuada para verificação em campo e não ajuste direto incondicional.",
                            section="Resumo Executivo (1.2)",
                        )
                    )
        return violations


class WeightsConservationRule(PreMarkdownRule):
    """Rule 7: Validates that sum of weights per station equals 100.0% +/- 0.1%."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        ctx = context or {}
        analyses = ctx.get("analyses", [])
        if analyses:
            for an in analyses:
                aid = an.get("agent_id") or "ESTACAO"
                features = an.get("features", [])
                if features:
                    total_w = sum(float(f.get("importance", 0.0)) for f in features)
                    total_pct = total_w * 100.0 if total_w <= 1.05 else total_w
                    if abs(total_pct - 100.0) > 0.1:
                        violations.append(ReportViolation(error_class=7, title="Soma dos Pesos Inválida", message=f"A soma dos pesos da estação '{aid}' totaliza {total_pct:.2f}% (esperado: 100,0% ± 0,1%).", section="Fichas de Explicabilidade (Anexo I)"))
        for s in report_data.get("sensors", []):
            xai_weights = s.get("xai_weights")
            if isinstance(xai_weights, dict):
                total_w = sum(float(v) for v in xai_weights.values())
                total_pct = total_w * 100.0 if total_w <= 1.05 else total_w
                if abs(total_pct - 100.0) > 0.1:
                    violations.append(ReportViolation(error_class=7, title="Soma dos Pesos Inválida", message=f"A soma dos pesos da estação '{s.get('id')}' totaliza {total_pct:.2f}% (esperado: 100,0% ± 0,1%).", section="Fichas de Explicabilidade (Anexo I)"))
        return violations


class AvailabilityConciliationRule(PreMarkdownRule):
    """Rule 8: Conciliates declared availability with cycle losses from sensor cards."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        exec_summary = report_data.get("executive_summary")
        if isinstance(exec_summary, dict) and "consolidated_availability" in exec_summary:
            eval_total = sum(int(s.get("eval_count", 120)) for s in sensors)
            appr_total = sum(int(s.get("approved_count", s.get("eval_count", 120))) for s in sensors)
            if eval_total > 0:
                calc_avail = (appr_total / eval_total) * 100.0
                decl_avail = float(exec_summary["consolidated_availability"])
                if abs(calc_avail - decl_avail) > 0.2:
                    violations.append(
                        ReportViolation(
                            error_class=8,
                            title="Divergência de Disponibilidade",
                            message=f"Disponibilidade declarada no Resumo ({decl_avail:.1f}%) diverge do cálculo pelas fichas ({calc_avail:.1f}%).",
                            section="Resumo Executivo (1.2)",
                        )
                    )
        return violations


class NormativeApplicabilityRule(PreMarkdownRule):
    """Rule 10: Asserts applicability of cited traffic norms (CONTRAN 798, NBR 14724 prohibition)."""

    def validate_pre(self, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        has_enforcement_radar = any(
            ("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower()) and
            (bool(s.get("is_enforcement")) or "fiscaliz" in str(s.get("purpose", "")).lower() or "autua" in str(s.get("purpose", "")).lower() or "fiscaliz" in str(s.get("equipmentType", "")).lower())
            for s in sensors
        )
        refs = report_data.get("references", [])

        if any("798" in str(r) for r in refs) and not has_enforcement_radar:
            violations.append(
                ReportViolation(
                    error_class=10,
                    title="Norma Inaplicável Citada",
                    message="A Resolução CONTRAN nº 798/2020 foi citada, mas inexistem medidores com finalidade declarada de fiscalização/autuação.",
                    section="Enquadramento Normativo e Referências",
                )
            )

        if any("14724" in str(r) for r in refs):
            violations.append(
                ReportViolation(
                    error_class=10,
                    title="Norma Proibida Citada",
                    message="A norma ABNT NBR 14724 (trabalhos acadêmicos) é inaplicável a relatórios técnicos executivos e está proibida.",
                    section="Enquadramento Normativo e Referências",
                )
            )
        return violations
