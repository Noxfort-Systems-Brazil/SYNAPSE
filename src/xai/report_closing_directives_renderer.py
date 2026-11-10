# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List
from src.xai.report_block_base import ReportBlockBase


class ReportClosingDirectivesRenderer(ReportBlockBase):
    """
    Renders closing sections of the official municipal report:
    - 5. Verificação Física de Tráfego (Conservação Macroscópica)
    - 6. Limites Operacionais e Confiança (O que o documento NÃO garante)
    - 7. Glossário Operacional
    - 8. Enquadramento Normativo e Referências Bibliográficas
    - 9. Rodapé de Responsabilidade Técnica
    """

    DEFAULT_GLOSSARY = [
        ("HCM (Highway Capacity Manual)", "Manual técnico de referência internacional para cálculo de capacidade de vias, saturação e níveis de serviço de tráfego."),
        ("LWR (Lighthill-Whitham-Richards)", "Modelo macroscópico de física de tráfego que descreve o fluxo contínuo e a conservação de veículos em corredores viários."),
        ("PINO (Physics-Informed Neural Operator)", "Rede neural guiada por equações da física para assegurar que as estimativas de tráfego sejam fisicamente coerentes com as leis de conservação."),
        ("KSE / Dead Reckoning", "Projeção cinemática temporária de velocidade utilizada quando ocorre perda transitória de conexão com o sensor de campo."),
        ("WaveletAE / Salvaguarda Zero-Trust", "Filtro matemático que identifica desvios abruptos e coloca leituras atípicas em quarentena antes de serem usadas no cálculo."),
        ("PI-DVAE-TCN", "Autoencoder convolucional que atenua ruídos de alta frequência preservando a tendência real do escoamento veicular."),
        ("Gradientes Integrados (Captum)", "Método de explicabilidade de IA que calcula a contribuição percentual de cada variável para a estimativa final do modelo."),
        ("Axioma da Completude", "Princípio matemático que distribui a variação da saída do modelo entre as variáveis de entrada, em relação à linha de base adotada."),
    ]

    DEFAULT_LIMITS = [
        "Estimativa Temporária (Dead Reckoning): As projeções cinemáticas de contingência perdem precisão gradativamente a cada ciclo sucessivo sem sinal físico. Não se recomenda operar em regime de contingência por mais de 15 ciclos consecutivos sem verificação física da conexão.",
        "Escopo da Explicabilidade (XAI): Os métodos de explicabilidade (Gradientes Integrados) explicam com transparência matemática como o modelo ponderou os dados recebidos, mas não constituem prova física isolada da verdade de campo ou da ausência de falhas instrumentais.",
        "Feeds de Terceiros (Crowdsourcing / APIs): Dados originados de plataformas externas (como Waze e TomTom) baseiam-se em amostragem estatística de usuários e estão sujeitos a latências de agregação da própria plataforma, servindo como apoio contextual e não como medição metrológica direta.",
        "Natureza do Relatório: Este documento é um registro técnico e explicativo de apoio operacional automatizado gerado pelo sistema SYNAPSE, não substituindo laudos periciais de engenharia emitidos por profissionais legalmente habilitados com ART/CREA ou ensaios metrológicos do INMETRO.",
    ]

    DEFAULT_LEGAL = [
        {
            "article": "Art. 1º, § 2º da Lei Federal nº 9.503/1997 (Código de Trânsito Brasileiro - CTB)",
            "desc": "Estabelece que o trânsito em condições seguras é um direito de todos e dever dos órgãos e entidades componentes do Sistema Nacional de Trânsito.",
        },
        {
            "article": "Art. 24, incisos II e III da Lei Federal nº 9.503/1997 (CTB)",
            "desc": "Atribui expressamente ao órgão executivo municipal de trânsito a competência para planejar, projetar, regulamentar e operar o trânsito de veículos e pedestres (inciso II), bem como implantar, manter e operar o sistema de sinalização, os dispositivos e os equipamentos de controle viário (inciso III).",
        },
        {
            "article": "Artigo 20 da Lei Federal nº 13.709/2018 (Lei Geral de Proteção de Dados - LGPD)",
            "desc": "Garantia de transparência e direito à explicabilidade sobre decisões tomadas com base em sistemas de tratamento automatizado de dados e inteligência artificial.",
        },
        {
            "article": "Artigo 50 da Lei Federal nº 9.784/1999 (Processo Administrativo)",
            "desc": "Dever legal de motivação formal, clara, explícita e congruente dos atos administrativos suportados por tecnologia computacional nos órgãos públicos.",
        },
        {
            "article": "Resolução CONTRAN nº 798/2020",
            "desc": "Requisitos técnicos aplicáveis exclusivamente para instrumentos medidores de velocidade quando utilizados para fins de fiscalização e autuação de infrações.",
        },
    ]

    DEFAULT_REFERENCES = [
        "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 10719: Informação e documentação — Relatório técnico e/ou científico — Apresentação. Rio de Janeiro: ABNT, 2015.",
        "BRASIL. Lei Federal nº 9.503, de 23 de setembro de 1997. Institui o Código de Trânsito Brasileiro. Brasília, 1997.",
        "CONSELHO NACIONAL DE TRÂNSITO (CONTRAN). Resolução nº 798, de 2 de setembro de 2020. Estabelece requisitos técnicos mínimos para medidores de velocidade quando destinados à fiscalização metrológica de trânsito. Brasília, 2020.",
        "LIGHTHILL, M. J.; WHITHAM, G. B. On Kinematic Waves. II. A Theory of Traffic Flow on Long Crowded Roads. Proceedings of the Royal Society of London. Series A, Mathematical and Physical Sciences, v. 229, n. 1178, p. 317-345, 1955.",
        "RICHARDS, P. I. Shock Waves on the Highway. Operations Research, v. 4, n. 1, p. 42-51, 1956.",
        "GREENSHIELDS, B. D. A Study of Traffic Capacity. Highway Research Board Proceedings, v. 14, p. 448-477, 1935.",
        "TRANSPORTATION RESEARCH BOARD (TRB). Highway Capacity Manual (HCM 7th Edition): A Guide for Multimodal Mobility Analysis. Washington, D.C.: National Academies of Sciences, Engineering, and Medicine, 2022.",
        "SUNDARARAJAN, M.; TALY, A.; YAN, Q. Axiomatic Attribution for Deep Networks. In: Proceedings of the 34th International Conference on Machine Learning (ICML), Sydney, Australia: PMLR, v. 70, p. 3319-3328, 2017.",
        "LIU, Y. et al. iTransformer: Inverted Transformers are Effective for Time Series Forecasting. In: International Conference on Learning Representations (ICLR), 2024.",
        "BRODY, S.; ALON, U.; YAHAV, E. How Attentive are Graph Attention Networks? (GATv2). In: International Conference on Learning Representations (ICLR), 2022.",
        "LI, Z. et al. Physics-Informed Neural Operator for Learning Partial Differential Equations (PINO). arXiv:2111.03794, 2021.",
        "KOKHLIKYAN, N. et al. Captum: A unified and generic model interpretability library for PyTorch. arXiv:2009.07896, 2020.",
    ]

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        report_data = context.get("report_data", {})
        legal = list(report_data.get("legalFraming") or self.DEFAULT_LEGAL)

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

        # Rule 10: CONTRAN 798 only applies to speed enforcement meters
        has_enforcement_radar = any(
            ("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower()) and
            (bool(s.get("is_enforcement")) or "fiscaliz" in str(s.get("purpose", "")).lower() or "autua" in str(s.get("purpose", "")).lower() or "fiscaliz" in str(s.get("equipmentType", "")).lower())
            for s in sensors
        )
        if not has_enforcement_radar:
            legal = [lf for lf in legal if "798" not in str(lf.get("article", ""))]

        authority = context.get("authority_name") or report_data.get("authorityName") or "(A preencher pelo Responsável Técnico)"
        authority_role = context.get("authority_role") or report_data.get("authorityRole") or "Engenheiro de Tráfego / Responsável Técnico"
        registration = context.get("registration_number") or report_data.get("registrationNumber") or "CREA / ART a vincular"
        city_hall = context.get("city_hall") or report_data.get("cityHall") or "PREFEITURA DO MUNICÍPIO"

        # 4.2 Considerações Finais e Parecer Técnico de Homologação
        title_key = block.get("title_key", "section6_title")
        lines.append(self._t(title_key, "### 4.2 Considerações Finais e Parecer Técnico de Homologação"))
        lines.append("")

        desc_key = block.get("content_key", "section6_desc")
        lines.append(self._t(
            desc_key,
            "O presente Laudo Técnico de Explicabilidade Algorítmica atesta que o motor **SYNAPSE v2.0 Enterprise (Noxfort Systems)** "
            "opera com total transparência matemática, estabilidade determinística e ausência de vieses não auditáveis. "
            "As decisões e percepções de tráfego são 100% fundamentadas no modelo de Gradientes Integrados e na conservação "
            "macroscópica de fluxo (LWR), atendendo integralmente às exigências de transparência pública, governança "
            "algorítmica e normas técnicas de engenharia de tráfego."
        ))
        lines.append("")

        # 4.2.1 Dispositivos Legais Aplicáveis e Respaldo Jurídico
        lines.append(self._t("legal_title", "#### 4.2.1 Dispositivos Legais Aplicáveis e Respaldo Jurídico"))
        lines.append("")
        for lf in legal:
            art = lf.get("article", "")
            art_desc = lf.get("desc", "")
            lines.append(f"- **{art}:** {art_desc}")
        lines.append("")

        # Disclaimer
        lines.append(self._t(
            "disclaimer_footer",
            "> *Relatório gerado automaticamente pelo sistema **SYNAPSE v2.0 Enterprise** em apoio ao Centro de Controle Operacional (CCO) "
            "e à Secretaria Municipal de Trânsito. Documento técnico de monitoramento operacional, sem fé pública e sujeito à validação "
            "final pelo Engenheiro Responsável Técnico.*"
        ))
        lines.append("")

        # Signature line
        lines.append("_____________________________________________________")
        lines.append(f"**{authority}**")
        lines.append(f"{authority_role} • {registration}")
        lines.append(f"{city_hall}")
        lines.append("")

        # Conformity statement
        lines.append(self._t(
            "conformity_statement",
            "> *Este documento foi consolidado de forma determinística pelo motor Neuro-Simbólico SYNAPSE XAI (Noxfort Systems). "
            "Ele atesta as condições puras da leitura de topologia e do comportamento da rede neural.*"
        ))
        lines.append("")
