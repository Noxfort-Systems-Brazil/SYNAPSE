# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Canonical Mathematical Formulations and Perception Equations (A.1 to A.5).

SOLID Compliance:
- [SRP] Encapsulates immutable, reviewed mathematical equations and explanatory parameters.
- Free of dynamic template mutation or fragile interpolation risks.
"""

from typing import Any, Dict, List


class CanonicalReportEquations:
    """Immutable reviewed equations block for ABNT traffic audit reports."""

    EQUATIONS: List[Dict[str, Any]] = [
        {
            "tag": "2.2.1",
            "title": "#### 2.2.1 Grau de Saturação e Relação Fundamental de Fluxo",
            "desc": "Relação macroscópica de tráfego entre volume de demanda, capacidade efetiva da via e velocidade média espacial:",
            "formula": r"$$ x = \frac{V}{c}, \quad q = \rho \cdot v \tag{2.2.1} $$",
            "params": (
                "Onde **x** é o grau de saturação da seção, **V** é o volume de tráfego atendido (veíc/h), "
                "**c** é a capacidade da via, **q** é a taxa de fluxo, **ρ** é a densidade de veículos (veíc/km) "
                "e **v** é a velocidade (km/h; para fontes de velocidade pontual, o valor é usado como aproximação da velocidade espacial)."
            ),
        },
        {
            "tag": "2.2.2",
            "title": "#### 2.2.2 Equação de Conservação Macroscópica de Tráfego (LWR / PINO)",
            "desc": "Garante a conservação física do fluxo veicular ao longo da via, impedindo que veículos sejam artificialmente criados ou eliminados:",
            "formula": r"$$ \frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v(\rho))}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right) \tag{2.2.2} $$",
            "params": (
                "Onde **∂ρ/∂t** é a taxa de variação da densidade no tempo, **∂(ρ·v)/∂x** é o gradiente espacial de fluxo, "
                "**v_f** é a velocidade de fluxo livre da via e **ρ_jam** é a densidade máxima de engarrafamento."
            ),
        },
        {
            "tag": "2.2.3",
            "title": "#### 2.2.3 Fusão Multivariada por Atenção Inter-Sensores (iTransformer)",
            "desc": "Correlação mútua entre as séries temporais de detectores heterogêneos ponderada pelo mecanismo de atenção neural:",
            "formula": r"$$ \text{Atenção}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_{\text{model}}}}\right) V \tag{2.2.3} $$",
            "params": (
                "Onde **Q, K e V** são as projeções de consulta, chave e valor das séries temporais de cada sensor "
                "e **d_model** é a dimensão do espaço latente."
            ),
        },
        {
            "tag": "2.2.4",
            "title": "#### 2.2.4 Atribuição por Gradientes Integrados (Método Captum)",
            "desc": "Decomposição matemática da contribuição de cada variável sensorial para a estimativa do estado de tráfego:",
            "formula": r"$$ \text{GradientesIntegrados}_i(x) = (x_i - x'_i) \times \int_{0}^{1} \frac{\partial F(x' + \alpha(x - x'))}{\partial x_i} d\alpha \tag{2.2.4} $$",
            "params": (
                "Onde **x_i** é a leitura atual do sensor i, **x'_i** é o vetor basal neutro de referência (fluxo livre), "
                "**F(x)** é a estimativa de estado de tráfego produzida pelo modelo neural SYNAPSE "
                "e **α** é o parâmetro de interpolação linear ao longo do caminho de integração."
            ),
            "completeness_axiom": "A consistência da atribuição é respaldada pelo **Axioma da Completude**:",
            "completeness_formula": r"$$ \sum_{i=1}^{n} \text{GradientesIntegrados}_i(x) = F(x) - F(x') $$",
            "completeness_desc": "Distribui a variação da estimativa do modelo entre as variáveis de entrada, em relação à linha de base adotada, satisfazendo o axioma da completude.",
        },
        {
            "tag": "2.2.5",
            "title": "#### 2.2.5 Estimador Cinemático de Estado (Dead Reckoning com Amortecimento)",
            "desc": "Projeção cinemática temporária de velocidade em caso de perda breve de pacotes ou isolamento de ruído:",
            "formula": r"$$ v_t = v_{t-1} + a_{t-1} \cdot \Delta t \cdot e^{-\lambda \Delta t} \tag{2.2.5} $$",
            "params": (
                "Onde **v_t** é a velocidade estimada no instante t, **a_{t-1}** é a aceleração precedente, "
                "**Δt** é o passo de amostragem (1,0s) e **λ** é o fator de amortecimento de segurança para decaimento suave."
            ),
        },
    ]
