# 🧠 SYNAPSE: Нейросетевой стек MARKVART™ и математические модели

Данный документ содержит математические формулировки, функции потерь и спецификации операторов PyTorch для 10 нейронных сетей и детерминированного пространственного движка, входящих в состав экосистемы **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers).

⬅️ [Главный Хаб](README.md) | 🗂️ [Сущности домена](domain_entities.md) | ⏱️ [Фазы выполнения](execution_phases.md)

---

## 1. Функциональная структура MARKVART™

10 нейросетевых архитектур и детерминированный движок пространственной привязки распределены по трем синергетическим уровням:

| Модель | Подсистема / Агент | Математическая парадигма | Основное назначение |
|:---|:---|:---|:---|
| **PINO-Traffic** | Непрерывный оператор | Нейросетевой оператор Фурье (FNO) + ДУЧП LWR | Моделирование непрерывной плотности и ударных волн. |
| **PI-DeepONet** | Оценщик полей | Двухсетевая архитектура Branch-Trunk | Нелинейное бесконечномерное отображение полей скорости. |
| **iTransformer** | Многомерная агрегация | Инвертированное внимание по токенам времени | Пространственная конвергенция датчиков без перекрестных шумов. |
| **GATv2 Lite** | Графовый анализ | Динамическое пространственно-временное внимание | Распространение заторовых волн между узлами сети. |
| **WaveletAE-OCC**| Фильтр аномалий | Дискретное вейвлет-преобразование (DWT) + Автоэнкодер | Обнаружение высокочастотных помех и кибератак. |
| **PatchTST** | Патч-прогнозирование | Сегментация рядов + Независимое внимание | Многошаговый прогноз скорости и занятости полос. |
| **TCNAE** | Сжатие признаков | 1D причинно-следственные расширенные свертки | Компактное представление временных рядов индуктивных петель. |
| **TimesNet** | Анализ периодичности | 2D разложение Фурье + Блоки Inception | Захват суточной и недельной цикличности городского трафика. |
| **FastMapMatcher** | Пространственная привязка | R-Tree индекс + метрика Фреше (CPU) | Детерминированное субмикросекундное совмещение полилиний с графом дорог SUMO. |
| **PI-DVAE-TCN** | Оценка неопределенности | Вариационный автоэнкодер с физическими связями | Количественная оценка эпистемической неопределенности. |
| **Qwen3 Jurist** | Когнитивное объяснение | Локальная малая модель (SLM) в формате GGUF 4-bit | Формирование юридически значимых текстовых обоснований. |

---

## 2. Физически информированные нейросетевые операторы

### PINO-Traffic (Physics-Informed Neural Operator)
- **Модуль**: `src/models/pino_traffic.py`
- **Фундаментальный закон**: Уравнение переноса Лайтхилла-Уизема-Ричардса (LWR):

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### Физическая невязка (Residual Loss):
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (Аппроксиматор непрерывных операторов)
- **Модуль**: `src/models/pi_deeponet.py`
- Отображает граничные условия через сеть **Branch** $b(u)$, а точки запроса через сеть **Trunk** $t(y)$:

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. Высокопроизводительная агрегация данных

### iTransformer (Инвертированное внимание)
- **Модуль**: `src/models/itransformer.py`
В отличие от классических трансформеров, **iTransformer** проецирует весь временной ряд отдельного датчика как единый токен:

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

### GATv2 Lite (Динамическое графовое внимание)
- **Модуль**: `src/models/gatv2_lite.py`
Динамически рассчитывает веса влияния между соседними перекрестками:

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k\right)\right)}$$

---

## 4. Юридический аудит и Qwen3 Jurist

Модель **Qwen3 Jurist** выполняется локально с помощью llama.cpp в формате 4-битной квантования GGUF, формируя экспертные протоколы на естественном языке при обнаружении аномалий или приоритетных фаз движения.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
