# 🧠 SYNAPSE: MARKVART™ 深度神经网络群与数学公式

本规范详细阐述 **MARKVART™**（变分注意力与循环 Transformer 模块化自适应推理核心）生态中集成的 10 个深度神经网络架构与确定性空间匹配引擎的数学表述、损失函数及 PyTorch 算子实现。

⬅️ [文档总中心](README.md) | 🗂️ [领域实体拓扑](domain_entities.md) | ⏱️ [执行阶段机制](execution_phases.md)

---

## 1. MARKVART™ 神经网络体系分类

10 个神经网络与确定性空间索引引擎协同分布于感知、拓扑与流体力学三个层级：

| 模型名称 | 所属子系统 / 代理 | 数学范式 | 核心工程职责 |
|:---|:---|:---|:---|
| **PINO-Traffic** | 连续物理算子 | 傅里叶神经算子 (FNO) + LWR 偏微分守恒方程 | 连续宏观交通流密度推演与激波形成模拟。 |
| **PI-DeepONet** | 场估计器 | 双分支 Branch-Trunk 深度算子网络 | 复杂拓扑下速度场算子的无限维非线性映射。 |
| **iTransformer** | 多变量时空融合 | 颠倒维度时间 Token 自注意力机制 | 多传感器时空特征融合，杜绝通道交叉干扰。 |
| **GATv2 Lite** | 图拓扑推理 | 动态多头时空图注意力网络 | 跨路口拥堵队列与绿波带相关性推演。 |
| **WaveletAE-OCC**| 异常感知卫士 | 离散小波变换 (DWT) + 单类自编码器 | 高频脉冲噪声过滤、传感器毛刺与攻击识别。 |
| **PatchTST** | 子序列补丁预测 | 时间序列分块补丁 + 通道独立 Transformer | 多步前向车速与车道占有率精确外推。 |
| **TCNAE** | 紧凑潜在特征 | 因果膨胀一维卷积 + 残差门控单元 | 线圈长时序原始数据的高效潜在表征压缩。 |
| **TimesNet** | 周期性特征提取 | 2D 傅里叶空间分解 + Inception 模块 | 城市交通流早晚高峰与周期性规律捕获。 |
| **FastMapMatcher** | 空间对齐引擎 | CPU R-Tree 空间索引 + Fréchet 距离度量 | 亚微秒级确定性几何匹配，将外部折线精确投影至 SUMO 路网中心线。 |
| **PI-DVAE-TCN** | 不确定性评估 | 物理守恒约束的变分自编码器 | 量化认知不确定性与数据偶然不确定性。 |
| **Qwen3 Jurist** | 认知解释生成 | 本地 4-bit 量化 GGUF 紧凑大模型 (SLM) | 自动生成符合法务与司法审计标准的文本报告。 |

---

## 2. 融入物理机理的神经算子 (Physics-Informed)

### PINO-Traffic (物理融合傅里叶神经算子)
- **代码模块**：`src/models/pino_traffic.py`
- **控制方程**：Lighthill-Whitham-Richards (LWR) 连续性守恒偏微分方程：

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### 物理残差损失函数：
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (深度连续算子网络)
- **代码模块**：`src/models/pi_deeponet.py`
- 通过 **Branch 分支网络** $b(u)$ 编码边界初值，通过 **Trunk 主干网络** $t(y)$ 编码空间坐标：

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. 高性能时空特征融合

### iTransformer (倒置注意力架构)
- **代码模块**：`src/models/itransformer.py`
将单个传感器的全长时序序列独立映射为注意力空间的一个 Token：

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

### GATv2 Lite (动态路网图注意力)
- **代码模块**：`src/models/gatv2_lite.py`
动态求解路段邻接节点的注意力权重系数：

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k\right)\right)}$$

---

## 4. Qwen3 Jurist 审计与认知解释

**Qwen3 Jurist** 依托本地 llama.cpp 引擎（4-bit GGUF 格式）离线执行，在检测到重大交通突发事件或控制机申请相位干预时，秒级生成清晰严密的中文因果归因与技术说明。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
