# ⏱️ SYNAPSE: ADAGIO™ 执行阶段机制与 KSE 运动学推算

本规范详细定义 **ADAGIO™**（自适应分布式自主图接入与优化）引擎的生命周期流转流程及 **KSE**（运动学状态估计）航位推算补偿算法。

⬅️ [文档总中心](README.md) | 🧠 [MARKVART™ 神经网络群](neural_models.md) | ⚡ [数据采集与 HFT](data_ingestion_and_hft.md)

---

## 1. ADAGIO™ 三阶段执行流程

SYNAPSE 系统严格遵循三个按序流转的阶段：

```
┌────────────────────────────────┐
│   阶段 0: AutoML 超参寻优      │  ◄── 基于 Optuna 的贝叶斯全局超参数优化
└───────────────┬────────────────┘
                │ 核心指标收敛
┌───────────────▼────────────────┐
│   阶段 1: 黄金数据集引导       │  ◄── 历史路况日志摄入与基准参数自校准
└───────────────┬────────────────┘
                │ 幽灵文件防破坏验证
┌───────────────▼────────────────┐
│   阶段 2: 四线程在线并发运行   │  ◄── 高频实时流式推理与决策推送
└────────────────────────────────┘
```

### 阶段 0: AutoML 自动化调优
- 利用 **Optuna** 框架自动搜索各神经网络的最佳结构超参：学习率、FNO 傅里叶截断阶数 ($k_{\max} \in [8, 32]$) 及 GATv2 多头注意力数。
- 借助 `MedianPruner` 动态剔除早期发散试验，大幅缩短冷启动训练时间。

### 阶段 1: 黄金数据集 (Golden Dataset) 引导
- 批量加载历史车流记录、OpenStreetMap 真实路网几何图和固定线圈历史均值。
- 构建数学自洽且平滑的城市路网基础状态张量。
- **幽灵文件机制 (Ghost-File)**：所有编译出的张量先写入临时隐藏文件，经 SHA-256 哈希校验完好后方可原子重命名为正式缓存，防止意外断电导致模型损坏。

### 阶段 2: 在线并发四线程运行时
正式运行环境中，系统激活四个非阻塞异步核心线程：

1. **数据摄入线程**：多协议监听 HTTP/MQTT/WebSocket，核验贝叶斯可信度。
2. **运动学推算线程 (KSE)**：在检测到现场传感器丢包时，采用卡尔曼滤波器持续外推车辆速度与位移。
3. **神经网络推理线程**：在 GPU 上通过独立 CUDA 流并发执行 MARKVART™ 推理。
4. **HFT 传输推流线程**：将密度矩阵打包为 Protobuf 格式，通过 gRPC 极速推向 CARINA 控制机。

---

## 2. KSE 运动学状态估计 (航位推算)

当城市道路传感器因网络闪断发生瞬时丢包时，**KSE 航位推算**保障感知数据平滑连续：

### 离散卡尔曼状态向量
$$\mathbf{x}_k = \begin{bmatrix} s_k \\ v_k \\ a_k \end{bmatrix}$$

其中 $s_k$ 为路段纵向位移，$v_k$ 为车流速度，$a_k$ 为车流加速度。

### 状态转移矩阵：
$$\mathbf{x}_{k+1} = \mathbf{F} \mathbf{x}_k + \mathbf{w}_k$$

$$\mathbf{F} = \begin{bmatrix} 1 & \Delta t & \frac{1}{2}\Delta t^2 \\ 0 & 1 & \Delta t \\ 0 & 0 & 1 \end{bmatrix}, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$

若传感器连续 $N_{\text{missed}} \ge 3$ 个周期未返回数据，系统将由 KSE 估计值平滑接管，并将传感器状态降级为 `FALLBACK`。

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
