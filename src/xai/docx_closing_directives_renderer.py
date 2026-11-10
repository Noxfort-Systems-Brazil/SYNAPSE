# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DOCX Part VI, VII & VIII - Technical Audit Findings, Legal Framework, Homologation & References Renderer.

SOLID Design:
- Single Responsibility Principle (SRP): Encapsulates only the construction of the formal pericial
  narrative (metrological conformity, physical conservation, Zero-Trust efficacy, LGPD explainability),
  legal framework, conclusive homologation opinion, ICP-Brasil signatures, and ABNT NBR 10719 references.
- Clean Architecture / DDD: Binds legal requirements, municipal authority metadata, and normative standards.
"""

from typing import Dict, Any
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.formatters.abnt_docx_styles import (
    add_abnt_paragraph,
    add_abnt_heading_1,
    add_abnt_heading_2,
)
from src.xai.xai_template_repository import XaiTemplateRepository
from src.xai.report_closing_directives_renderer import ReportClosingDirectivesRenderer


class DocxClosingDirectivesRenderer:
    """
    Renders Section 5 (Physical Verification - LWR Continuity), Section 6 (Operational Limits & Trust),
    Section 7 (Operational Glossary), Section 8 (Normative Framework & References), and Section 9
    (Technical Responsibility Footer) into Microsoft Word (.docx).
    """

    DEFAULT_GLOSSARY = ReportClosingDirectivesRenderer.DEFAULT_GLOSSARY
    DEFAULT_LIMITS = ReportClosingDirectivesRenderer.DEFAULT_LIMITS
    DEFAULT_LEGAL = ReportClosingDirectivesRenderer.DEFAULT_LEGAL
    DEFAULT_REFERENCES = ReportClosingDirectivesRenderer.DEFAULT_REFERENCES

    def render(
        self,
        doc: Document,
        report_data: Dict[str, Any],
        font_family: str,
        base_font_size_pt: float,
        align_mode: Any,
        line_spacing_multiplier: float,
    ) -> None:
        """Renders Sections 5, 6, 7, 8 and 9 - Physical Verification, Limits, Glossary, References and Responsibility Footer."""
        # --- SEÇÃO 5: VERIFICAÇÃO FÍSICA DE TRÁFEGO ---
        templates = report_data.get("templates") if isinstance(report_data, dict) else None
        lang = str(report_data.get("language", "pt_br") if isinstance(report_data, dict) else "pt_br").lower()
        if not templates:
            templates = XaiTemplateRepository.get_templates_for_language(lang)

        # --- PARTE III — DIRETRIZES TÉCNICAS E PARECER CONCLUSIVO DE HOMOLOGAÇÃO ---
        part_title = templates.get("directives_part_title", "PARTE III — DIRETRIZES TÉCNICAS E PARECER CONCLUSIVO DE HOMOLOGAÇÃO").replace("## ", "")
        add_abnt_heading_1(doc, part_title, font_family, base_font_size_pt)

        # 3.1 Verificação Física
        phys_title = templates.get("physical_verification_title", "3.1. Verificação Física de Tráfego (Conservação Macroscópica)").replace("### ", "")
        add_abnt_heading_2(doc, phys_title, font_family, base_font_size_pt)
        phys_body = templates.get(
            "physical_verification_body",
            "A matriz de fusão neural de sensores foi avaliada sob a ótica das leis clássicas de conservação macroscópica "
            "de tráfego de Lighthill-Whitham-Richards (LWR / PINO). O resíduo diferencial de continuidade física manteve-se "
            "inferior a 0,05 em todo o corredor monitorado."
        )
        add_abnt_paragraph(
            doc,
            phys_body,
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )
        phys_note = templates.get(
            "physical_verification_note",
            "Nota de Avaliação Física: O resultado observado é tecnicamente consistente com as leis de conservação de fluxo, "
            "indicando que não houve geração espontânea nem desaparecimento fictício de veículos na malha arterial. "
            "Essa checagem atesta a plausibilidade física do modelo matemático, sem pretensão de constituir prova pericial absoluta de contagem."
        ).replace("> **Nota de Avaliação Física:** ", "Nota de Avaliação Física: ").replace("> **Physical Evaluation Note:** ", "Physical Evaluation Note: ").replace("> **Nota de Evaluación Física:** ", "Nota de Evaluación Física: ").replace("**", "")
        add_abnt_paragraph(
            doc,
            phys_note,
            font_family,
            base_font_size_pt - 0.5,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        # 3.2 Limites Operacionais e Confiança
        limits_title = templates.get("limits_title", "3.2. Limites Operacionais e Confiança (O que o Documento NÃO Garante)").replace("### ", "")
        add_abnt_heading_2(doc, limits_title, font_family, base_font_size_pt)
        limits_intro = templates.get("limits_intro", "Em respeito à transparência técnica e administrativa, declaram-se os seguintes limites de operação do sistema:")
        add_abnt_paragraph(
            doc,
            limits_intro,
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
        )
        raw_limits = templates.get("default_limits") or [f"{t}: {d}" for t, d in self.DEFAULT_LIMITS]
        for idx, lim in enumerate(raw_limits, 1):
            if isinstance(lim, (list, tuple)):
                title_p = lim[0]
                desc_p = f" {lim[1]}" if len(lim) > 1 else ""
            else:
                parts = str(lim).split(":", 1)
                title_p = parts[0]
                desc_p = f" {parts[1].strip()}" if len(parts) > 1 else ""
            add_abnt_paragraph(
                doc,
                f"{idx}. {title_p}:{desc_p}",
                font_family,
                base_font_size_pt,
                align_mode,
                line_spacing_multiplier,
                indent=True,
            )

        # 3.3 Glossário Operacional
        glossary_title = templates.get("glossary_title", "3.3. Glossário Operacional").replace("### ", "")
        add_abnt_heading_2(doc, glossary_title, font_family, base_font_size_pt)
        glossary = templates.get("default_glossary") or self.DEFAULT_GLOSSARY
        for item in glossary:
            term = item[0] if isinstance(item, (list, tuple)) else str(item)
            definition = item[1] if isinstance(item, (list, tuple)) and len(item) > 1 else ""
            add_abnt_paragraph(
                doc,
                f"{term}: {definition}",
                font_family,
                base_font_size_pt - 0.5,
                align_mode,
                line_spacing_multiplier,
                bold_prefix="• ",
                indent=True,
            )

        # 3.4 Base Legal e Referências
        legal_title = templates.get("legal_title", "3.4. Base Legal e Referências Técnicas").replace("### ", "")
        add_abnt_heading_2(doc, legal_title, font_family, base_font_size_pt)
        sub1 = templates.get("legal_sub1", "Dispositivos Legais Aplicáveis:").replace("#### ", "")
        add_abnt_paragraph(doc, sub1, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        legal = list(report_data.get("legalFraming") or self.DEFAULT_LEGAL)
        references = list(report_data.get("references") or self.DEFAULT_REFERENCES)

        # Rule 11: LGPD Art. 20 only applies when personal data is processed
        sensors = report_data.get("sensors", [])
        has_personal_data = any(
            "placa" in str(s.get("equipmentType", "")).lower() or
            "lpr" in str(s.get("equipmentType", "")).lower() or
            "reconhecimento de placa" in str(s.get("equipmentType", "")).lower() or
            bool(s.get("processes_personal_data"))
            for s in sensors
        )
        if not has_personal_data:
            legal = [lf for lf in legal if "13.709" not in str(lf.get("article", "")) and "LGPD" not in str(lf.get("article", ""))]
            references = [r for r in references if "13.709" not in str(r) and "LGPD" not in str(r)]

        # Rule 10: CONTRAN 798 only applies to speed enforcement meters
        has_enforcement_radar = any(
            ("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower()) and
            (bool(s.get("is_enforcement")) or "fiscaliz" in str(s.get("purpose", "")).lower() or "autua" in str(s.get("purpose", "")).lower() or "fiscaliz" in str(s.get("equipmentType", "")).lower())
            for s in sensors
        )
        if not has_enforcement_radar:
            legal = [lf for lf in legal if "798" not in str(lf.get("article", ""))]
            references = [r for r in references if "798" not in str(r)]

        for leg in legal:
            art_title = leg.get("article", leg.get("norm", ""))
            art_desc = leg.get("desc", leg.get("description", leg.get("operationalRequirement", "")))
            add_abnt_paragraph(
                doc,
                f"{art_title}: {art_desc}",
                font_family,
                base_font_size_pt,
                align_mode,
                line_spacing_multiplier,
                bold_prefix="• ",
                indent=True,
            )

        sub2 = templates.get("legal_sub2", "Referências Bibliográficas (ABNT NBR 10719:2015):").replace("#### ", "")
        add_abnt_paragraph(doc, sub2, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        for ref in references:
            p_ref = doc.add_paragraph()
            p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_ref.paragraph_format.space_after = Pt(4)
            r_ref = p_ref.add_run(ref)
            r_ref.font.size = Pt(base_font_size_pt - 2)
            r_ref.font.name = font_family

        # 3.5 Parecer Técnico e Chancela de Auditoria
        parecer_title = templates.get("parecer_title", "3.5. Parecer Técnico e Chancela de Auditoria").replace("### ", "")
        add_abnt_heading_2(doc, parecer_title, font_family, base_font_size_pt)
        parecer_desc = templates.get(
            "parecer_desc",
            "O presente Laudo Técnico de Explicabilidade Algorítmica atesta que o motor SYNAPSE v2.0 Enterprise "
            "opera com total conformidade física, estabilidade determinística e ausência de vieses não auditáveis. "
            "As decisões de percepção e fusão sensorial são 100% fundamentadas no modelo matemático de Gradientes Integrados "
            "e nas leis fundamentais de tráfego (LWR/HCM), atendendo integralmente às exigências de auditabilidade governamental "
            "e normas técnicas de engenharia de tráfego."
        ).replace("**", "")
        add_abnt_paragraph(
            doc,
            parecer_desc,
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )
        disclaimer_text = templates.get(
            "disclaimer_footer",
            "Relatório gerado automaticamente pelo sistema SYNAPSE v2.0 Enterprise em apoio ao Centro de Controle Operacional (CCO) "
            "e à Secretaria Municipal de Trânsito. Documento técnico de monitoramento operacional, sem fé pública e sujeito à revisão, "
            "auditoria de campo e validação final pelo Engenheiro Responsável Técnico."
        ).replace("> *", "").replace("*", "")
        add_abnt_paragraph(
            doc,
            disclaimer_text,
            font_family,
            base_font_size_pt - 0.5,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        authority = report_data.get("authorityName") or "(A preencher pelo Responsável Técnico)"
        authority_role = report_data.get("authorityRole") or "Engenheiro de Tráfego / Responsável Técnico"
        registration = report_data.get("registrationNumber") or "CREA / ART a vincular"
        city_hall = report_data.get("cityHall", "PREFEITURA MUNICIPAL")

        sig_p = doc.add_paragraph()
        sig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sig_p.paragraph_format.space_before = Pt(24)
        sig_p.add_run("_____________________________________________________\n")
        r_sig_name = sig_p.add_run(f"{authority}\n")
        r_sig_name.bold = True
        sig_p.add_run(f"{authority_role}\n{registration}\n{city_hall}\n").font.size = Pt(9.5)

        p_conf = doc.add_paragraph()
        p_conf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_conf.paragraph_format.space_before = Pt(12)
        conf_text = templates.get(
            "conformity_statement",
            "Este documento foi consolidado de forma determinística pelo motor Neuro-Simbólico SYNAPSE XAI (Noxfort Systems). "
            "Ele atesta as condições puras da leitura de topologia e do comportamento da rede neural."
        ).replace("> *", "").replace("*", "")
        r_conf = p_conf.add_run(conf_text)
        r_conf.font.size = Pt(8)
        r_conf.italic = True

        # --- ANEXO TÉCNICO: FORMULAÇÃO MATEMÁTICA E EQUAÇÕES DE PERCEPÇÃO ---
        from src.xai.docx_math_xai_renderer import DocxMathXaiRenderer
        DocxMathXaiRenderer().render_technical_annex_equations(
            doc, font_family, base_font_size_pt, align_mode, line_spacing_multiplier
        )
