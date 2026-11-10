# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import pytest
from docx.shared import Cm
from src.services.traffic_report_service import TrafficReportService
from src.formatters.abnt_docx_exporter import AbntDocxExporter
from src.formatters.abnt_html_preview_exporter import AbntHtmlPreviewExporter
from src.handlers.system_handler import SystemCommandHandler
from src.ipc.ipc_protocol import IpcMessage


def _mock_sensors():
    return [
        {
            "id": "DET-01",
            "junction": "Av. Paulista x Al. Santos",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "22.5 km/h",
            "measuredFlow": "1.420 veíc/h",
            "saturationDegree": "0.72",
            "occupancyRate": "64.0%",
            "inmetroReport": "INMETRO 123",
            "operationalStatus": "Operação Nominal",
        }
    ]


def test_abnt_docx_exporter_margins_and_sections(tmp_path):
    service = TrafficReportService()
    report_output = service.build_report(override_sensors=_mock_sensors())
    report_data = report_output["report"]

    exporter = AbntDocxExporter()
    doc = exporter.generate(report_data, typography_options={"fontFamily": "Times New Roman", "lineSpacing": 1.5})

    section = doc.sections[0]
    assert abs(section.top_margin.cm - 3.0) < 0.05
    assert abs(section.left_margin.cm - 3.0) < 0.05
    assert abs(section.bottom_margin.cm - 2.0) < 0.05
    assert abs(section.right_margin.cm - 2.0) < 0.05

    # Check tables (Identification Table + Section 1.3 Synthetic Table + Section 1.4 Criteria Table + Section 4 Safety Table)
    assert len(doc.tables) >= 3

    full_docx_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Ementa" in full_docx_text
    assert "1.3 Quadro Sintético por Ponto de Monitoramento" in full_docx_text
    assert "ANEXO B — Fichas Técnicas Periciais" in full_docx_text or "ANEXO I" in full_docx_text
    assert "grau de saturação" in full_docx_text or "Grau de Saturação" in full_docx_text
    assert "2.2.1" in full_docx_text
    assert "2.2.5" in full_docx_text
    assert "DIRETRIZES TÉCNICAS E PARECER CONCLUSIVO" in full_docx_text
    assert "SYNAPSE v2.0 Enterprise" in full_docx_text

    # Check file export
    docx_file = str(tmp_path / "laudo_teste.docx")
    saved_path = exporter.export_to_file(report_data, docx_file)
    assert os.path.isfile(saved_path)
    assert os.path.getsize(saved_path) > 10000

    # Check bytes export
    data_bytes = exporter.export_to_bytes(report_data)
    assert isinstance(data_bytes, bytes)
    assert len(data_bytes) > 10000


def test_abnt_html_preview_exporter():
    service = TrafficReportService()
    report_output = service.build_report(
        override_sensors=_mock_sensors(),
        typography_options={"fontFamily": "Arial", "lineSpacing": 1.15},
    )
    
    assert "preview_html" in report_output
    preview = report_output["preview_html"]

    assert "abnt-container" in preview
    assert "abnt-page-sheet" in preview
    assert 'data-page="1"' in preview
    assert 'data-page="6"' in preview
    assert "1.3. Quadro Sintético de Auditoria por Estação Sensorial" in preview
    assert "3.2. Auditoria de Intervenções de Salvaguarda Zero-Trust" in preview
    assert "Equação A.1" in preview or "Equação 1" in preview
    assert "LWR / PINO" in preview
    assert "iTransformer" in preview
    assert "22.5 km/h" in preview
    assert report_output["report"]["protocol"] in preview


def test_report_handler_export_docx_ipc(tmp_path):
    from unittest.mock import MagicMock
    from src.handlers.report_handler import ReportCommandHandler
    mock_controller = MagicMock()
    mock_controller.app_state = MagicMock()

    docx_dest = str(tmp_path / "laudo_ipc_export.docx")
    msg = IpcMessage(
        id="export_req_1",
        action="export_official_report_docx",
        payload={
            "output_path": docx_dest,
            "municipal_config": {"cityHall": "PREFEITURA TESTE IPC"},
            "typography_options": {"fontFamily": "Arial", "lineSpacing": 1.5}
        }
    )

    # Step 1: No sensors -> Export blocked by lock guard
    mock_controller.app_state.get_all_data_sources.return_value = []
    handler = ReportCommandHandler(controller=mock_controller)
    resp = handler.handle_export_official_report_docx(msg)
    assert resp["success"] is False
    assert resp["ready"] is False
    assert "sendo gerados" in resp["error"]

    # Step 2: Sensors active -> Export proceeds and writes file
    mock_source = MagicMock(id="DET-01", name="Detector 1", source_type="Radar", last_speed=25.0)
    mock_controller.app_state.get_all_data_sources.return_value = [mock_source]
    resp2 = handler.handle_export_official_report_docx(msg)
    assert resp2["success"] is True
    assert resp2["output_path"] == docx_dest
    assert os.path.isfile(docx_dest)
    assert os.path.getsize(docx_dest) > 10000


def test_docx_visual_parity_logo_header(tmp_path):
    from PIL import Image
    from src.xai.docx_header_cover_renderer import DocxHeaderCoverRenderer
    from docx import Document

    logo_file = str(tmp_path / "brasao_teste.png")
    img = Image.new("RGB", (60, 60), color="blue")
    img.save(logo_file)

    doc = Document()
    renderer = DocxHeaderCoverRenderer()
    report_data = {
        "logo_path": logo_file,
        "city_hall": "PREFEITURA DE TESTE",
        "department": "SECRETARIA DE MOBILIDADE",
        "protocol": "PROT-2026-TEST",
        "processNumber": "PROC-001",
        "systemVersion": "v2.0 Enterprise",
    }
    renderer.render(doc, report_data, font_family="Arial", base_font_size_pt=11.0, dt_str="30/10/2026")

    # When logo_path is present and valid, first table is the 2-column header table
    assert len(doc.tables) >= 2
    hdr_table = doc.tables[0]
    assert len(hdr_table.columns) == 2
    assert len(hdr_table.rows) == 1
    assert "PREFEITURA DE TESTE" in hdr_table.cell(0, 1).text


def test_docx_visual_parity_lists_and_paragraphs():
    from src.formatters.markdown_to_docx import render_markdown_to_docx
    from docx import Document
    from docx.shared import Cm

    doc = Document()
    md_sample = (
        "- Item de lista bullet com descrição longa para validação de estilo nativo\n"
        "1. Primeiro item numerado com sequência ordinal\n"
        "> **Aviso Operacional:** Citação sem recuo de primeira linha.\n\n"
        "Este é um parágrafo narrativo longo o suficiente para ter mais de oitenta caracteres e receber recuo de primeira linha ABNT.\n\n"
        "Nota curta."
    )
    render_markdown_to_docx(doc, md_sample, default_font_size=11.0, font_name="Arial")

    styles = [p.style.name for p in doc.paragraphs if p.text]
    assert "List Bullet" in styles
    assert "List Number" in styles

    # Check long paragraph indentation and spacing
    long_p = [p for p in doc.paragraphs if "parágrafo narrativo longo" in p.text][0]
    assert abs(long_p.paragraph_format.first_line_indent.cm - 1.25) < 0.01
    assert long_p.paragraph_format.line_spacing == 1.5

    # Check short note does not get first line indent
    short_p = [p for p in doc.paragraphs if p.text == "Nota curta."][0]
    assert short_p.paragraph_format.first_line_indent is None


def test_docx_equation_builder_alphanumeric_tags():
    from src.formatters.docx_equation_builder import DocxEquationBuilder
    from docx import Document

    doc = Document()
    eq_line = "$$ v_t = v_{t-1} + a_{t-1} \\cdot \\Delta t \\tag{A.5} $$"
    rendered = DocxEquationBuilder.render_equation(doc, eq_line, default_font_size=11.0, font_name="Arial")
    assert rendered is True

    eq_p = doc.paragraphs[-1]
    assert "(A.5)" in eq_p.text
    assert "\\tag" not in eq_p.text

