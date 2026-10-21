# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Official Traffic Audit Report Domain Model (DDD: Entities & Value Objects).

Standardized domain entities and value objects for municipal traffic engineering audits,
ABNT NBR 10719 / NBR 14724 documentation, and CTB Art. 24 legal compliance.
Eliminates primitive obsession and ensures strict typing across services and presenters.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class NetworkSummary:
    monitored_junctions_count: int = 4
    total_sensors_online: int = 4
    average_corridor_speed: str = "18.4 km/h"
    global_saturation_index: str = "0,70"
    flow_state_label: str = "Estável / Controlado"
    total_hourly_flow: str = "4.800 veíc/h"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "NetworkSummary":
        d = data or {}
        return cls(
            monitored_junctions_count=int(d.get("monitoredJunctionsCount", d.get("controlledIntersections", 4))),
            total_sensors_online=int(d.get("totalSensorsOnline", d.get("totalSensorsCount", 4))),
            average_corridor_speed=str(d.get("averageCorridorSpeed", d.get("networkMeanSpeed", "18.4 km/h"))),
            global_saturation_index=str(d.get("globalSaturationIndex", str(d.get("networkMeanSaturation", "0,70")).split()[0])),
            flow_state_label=str(d.get("flowStateLabel", "Estável / Controlado")),
            total_hourly_flow=str(d.get("totalHourlyFlow", "4.800 veíc/h")),
        )


@dataclass
class CorridorLocation:
    corridor_name: str = "Corredor Arterial Central"
    jurisdiction: str = "Município de São Paulo / SMT"
    geographic_bounds: str = "Malha Arterial Monitorada"
    nominal_network_capacity: str = "28.000 veíc/h (1.800 veíc/h por faixa)"
    baseline_signal_plan: str = "Amostragem 1,0s • gRPC HFT-Link • Zero-Trust"

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]] = None) -> "CorridorLocation":
        d = data or {}
        return cls(
            corridor_name=str(d.get("corridorName", d.get("corridor", "Corredor Arterial Central"))),
            jurisdiction=str(d.get("jurisdiction", d.get("city", "Município de São Paulo / SMT"))),
            geographic_bounds=str(d.get("geographicBounds", "Malha Arterial Monitorada")),
            nominal_network_capacity=str(d.get("nominalNetworkCapacity", "28.000 veíc/h (1.800 veíc/h por faixa)")),
            baseline_signal_plan=str(d.get("baselineSignalPlan", "Amostragem 1,0s • gRPC HFT-Link • Zero-Trust")),
        )


@dataclass
class SensorReportItem:
    id: str
    junction: str
    equipment_type: str = "Sensor de Tráfego Homologado"
    measured_speed: str = "0.0 km/h"
    measured_flow: str = "0 veíc/h"
    occupancy_rate: str = "0.0%"
    saturation_degree: str = "0.00"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SensorReportItem":
        return cls(
            id=str(d.get("id", "")),
            junction=str(d.get("junction", "")),
            equipment_type=str(d.get("equipmentType", "Sensor de Tráfego")),
            measured_speed=str(d.get("measuredSpeed", "")),
            measured_flow=str(d.get("measuredFlow", "")),
            occupancy_rate=str(d.get("occupancyRate", "")),
            saturation_degree=str(d.get("saturationDegree", "")),
        )


@dataclass
class AttributionReportItem:
    detector_id: str
    parameter_name: str = ""
    junction_location: str = ""
    causal_weight_percent: float = 0.0
    gradient_direction: str = ""
    traffic_impact_analysis: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AttributionReportItem":
        return cls(
            detector_id=str(d.get("detectorId", "")),
            parameter_name=str(d.get("parameterName", "")),
            junction_location=str(d.get("junctionLocation", "")),
            causal_weight_percent=float(d.get("causalWeightPercent", 0.0)),
            gradient_direction=str(d.get("gradientDirection", "")),
            traffic_impact_analysis=str(d.get("trafficImpactAnalysis", "")),
        )


@dataclass
class SafetyInterventionItem:
    id: str = ""
    time_recorded: str = ""
    junction: str = ""
    equipment_id: str = ""
    irregularity_detected: str = ""
    corrective_guardrail: str = ""
    final_state: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SafetyInterventionItem":
        return cls(
            id=str(d.get("id", "")),
            time_recorded=str(d.get("timeRecorded", "")),
            junction=str(d.get("junction", "")),
            equipment_id=str(d.get("equipmentId", "")),
            irregularity_detected=str(d.get("irregularityDetected", "")),
            corrective_guardrail=str(d.get("correctiveGuardrail", "")),
            final_state=str(d.get("finalState", "")),
        )


@dataclass
class QuesitoItem:
    number: str
    question: str
    answer: str
    technical_justification: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any], default_idx: int = 1) -> "QuesitoItem":
        q_num = str(d.get("number", d.get("id", default_idx)))
        return cls(
            number=q_num,
            question=str(d.get("question", "")),
            answer=str(d.get("answer", "")),
            technical_justification=str(d.get("technicalJustification", "")),
        )


@dataclass
class LegalFramingItem:
    article: str
    description: str

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LegalFramingItem":
        return cls(
            article=str(d.get("article", d.get("norm", ""))),
            description=str(d.get("desc", d.get("description", d.get("operationalRequirement", "")))),
        )


@dataclass
class OfficialReportData:
    """
    Root Aggregate / Entity for Official Audit Reports.
    Provides complete typed accessors and implements duck-typing (dict-like get)
    for 100% backward compatibility.
    """
    protocol: str = "RELATORIO-TRAFEGO-2026"
    process_number: str = "PA-SMT-2026/0001"
    city_hall: str = "PREFEITURA DO MUNICÍPIO DE SÃO PAULO"
    department: str = "SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO"
    authority_name: str = "Gabriel Moraes"
    authority_role: str = "Autoridade de Trânsito / Auditor Pericial"
    registration_number: str = "Matrícula Funcional nº 84.102-3"
    system_version: str = "SYNAPSE v2.0 Enterprise"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    digital_certification: str = "AUTENTICADO-ICP-BRASIL-SYNAPSE-SEC-2026"
    audit_objective: str = "Auditar a fusão neural de sensores heterogêneos e a consistência metrológica da malha arterial em tempo real."
    observed_traffic_diagnosis: str = "Supervisão contínua da malha arterial pelo gateway."
    adaptive_action_executed: str = "Fusão neural multi-sensorial executada pelo modelo iTransformer + GATv2 com filtragem cinemática PI-DVAE-TCN e transmissão via HFT-Link gRPC."
    operational_supervision: str = "HOMOLOGAÇÃO DA OPERAÇÃO DE PERCEPÇÃO E FUSÃO NEURAL."
    counterfactual_analysis: str = "Cenário contrafactual analisado."
    network_summary: NetworkSummary = field(default_factory=NetworkSummary)
    location: CorridorLocation = field(default_factory=CorridorLocation)
    comparative_evolution: Dict[str, Any] = field(default_factory=dict)
    sensors: List[SensorReportItem] = field(default_factory=list)
    attributions: List[AttributionReportItem] = field(default_factory=list)
    safety_interventions: List[Any] = field(default_factory=list)
    quesitos: List[QuesitoItem] = field(default_factory=list)
    legal_framing: List[LegalFramingItem] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    raw_dict: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "OfficialReportData":
        if isinstance(raw, OfficialReportData):
            return raw

        r = raw or {}
        sensors = [SensorReportItem.from_dict(s) if isinstance(s, dict) else s for s in r.get("sensors", [])]
        attrs = [AttributionReportItem.from_dict(a) if isinstance(a, dict) else a for a in r.get("attributions", [])]
        quesitos = [QuesitoItem.from_dict(q, idx) if isinstance(q, dict) else q for idx, q in enumerate(r.get("quesitos", []), 1)]
        legal = [LegalFramingItem.from_dict(l) if isinstance(l, dict) else l for l in r.get("legalFraming", [])]

        return cls(
            protocol=str(r.get("protocol", "RELATORIO-TRAFEGO-2026")),
            process_number=str(r.get("processNumber", "PA-SMT-2026/0001")),
            city_hall=str(r.get("cityHall", "PREFEITURA DO MUNICÍPIO DE SÃO PAULO")),
            department=str(r.get("department", "SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO")),
            authority_name=str(r.get("authorityName", "Gabriel Moraes")),
            authority_role=str(r.get("authorityRole", "Autoridade de Trânsito / Auditor Pericial")),
            registration_number=str(r.get("registrationNumber", "Matrícula Funcional nº 84.102-3")),
            system_version=str(r.get("system", r.get("systemVersion", "SYNAPSE v2.0 Enterprise"))),
            timestamp=str(r.get("timestamp", datetime.now().isoformat())),
            digital_certification=str(r.get("digitalCertification", "AUTENTICADO-ICP-BRASIL-SYNAPSE-SEC-2026")),
            audit_objective=str(r.get("auditObjective", "Auditar a fusão neural de sensores heterogêneos e a consistência metrológica da malha arterial.")),
            observed_traffic_diagnosis=str(r.get("observedTrafficDiagnosis", "Supervisão contínua da malha arterial pelo gateway.")),
            adaptive_action_executed=str(r.get("adaptiveActionExecuted", "Fusão neural multi-sensorial executada pelo modelo iTransformer + GATv2.")),
            operational_supervision=str(r.get("operationalSupervision", "HOMOLOGAÇÃO DA OPERAÇÃO DE PERCEPÇÃO.")),
            counterfactual_analysis=str(r.get("counterfactualAnalysis", "Cenário contrafactual analisado.")),
            network_summary=NetworkSummary.from_dict(r.get("networkSummary")),
            location=CorridorLocation.from_dict(r.get("location")),
            comparative_evolution=r.get("comparativeEvolution", {}),
            sensors=sensors,
            attributions=attrs,
            safety_interventions=r.get("safetyInterventions", []),
            quesitos=quesitos,
            legal_framing=legal,
            references=list(r.get("references", [])),
            raw_dict=r,
        )

    # Duck-typing methods for full compatibility with legacy code calling report.get(...) or report[...]
    def get(self, key: str, default: Any = None) -> Any:
        if self.raw_dict and key in self.raw_dict:
            return self.raw_dict[key]
        mapping = {
            "protocol": self.protocol,
            "processNumber": self.process_number,
            "cityHall": self.city_hall,
            "department": self.department,
            "authorityName": self.authority_name,
            "authorityRole": self.authority_role,
            "registrationNumber": self.registration_number,
            "system": self.system_version,
            "systemVersion": self.system_version,
            "timestamp": self.timestamp,
            "digitalCertification": self.digital_certification,
            "auditObjective": self.audit_objective,
            "observedTrafficDiagnosis": self.observed_traffic_diagnosis,
            "adaptiveActionExecuted": self.adaptive_action_executed,
            "operationalSupervision": self.operational_supervision,
            "counterfactualAnalysis": self.counterfactual_analysis,
            "networkSummary": asdict(self.network_summary),
            "location": asdict(self.location),
            "comparativeEvolution": self.comparative_evolution,
            "sensors": [s if isinstance(s, dict) else asdict(s) for s in self.sensors],
            "attributions": [a if isinstance(a, dict) else asdict(a) for a in self.attributions],
            "safetyInterventions": self.safety_interventions,
            "quesitos": [q if isinstance(q, dict) else asdict(q) for q in self.quesitos],
            "legalFraming": [l if isinstance(l, dict) else asdict(l) for l in self.legal_framing],
            "references": self.references,
        }
        return mapping.get(key, default)

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None and key not in self.raw_dict:
            raise KeyError(key)
        return val

    def __contains__(self, key: str) -> bool:
        return (key in self.raw_dict) or (self.get(key) is not None)
